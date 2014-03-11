from abc import ABCMeta, abstractproperty, abstractmethod

from xblock.fields import List
from xmodule.modulestore import Location

from django.conf import settings
from django.core.urlresolvers import reverse

# We only need to scrape strings for i18n in this file, since ugettext is called on them in the template:
# https://github.com/edx/edx-platform/blob/master/lms/templates/courseware/course_navigation.html#L29
_ = lambda text: text

##### Tab class.
class CourseTab(object):
    __metaclass__ = ABCMeta

    def __init__(self, name, active_page_name, link_func):
        # name of the tab - may or may not be stored in the database
        self.name = name

        # used by UI layers to indicate which tab is active
        self.active_page_name = active_page_name

        # function that computes the link for the tab, given the course
        self.link_func = link_func

    @abstractmethod
    def type(self): pass

    def can_display(self, course, is_user_authenticated, is_user_staff):
        return True

    def get(self, key, default=None):
        if key == 'name':
            return self.name
        elif key == 'type':
            return self.type()
        elif key == 'active_page_name':
            return self.active_page_name
        else:
            return default

    def __getitem__(self, key):
        item = self.get(key=key, default=KeyError)
        if item is KeyError:
            raise KeyError()
        else:
            return item

    def __setitem__(self, key, value):
        # change values of the tab, except for 'type'
        if key == 'name':
            self.name = value
        elif key == 'active_page_name':
            self.active_page_name = value
        else:
            raise KeyError()

    @classmethod
    def validate(cls, tab):
        """
        Can be overridden by sub-classes that require params in the tab.
        """
        pass

    #  A factory function that takes an optional tab if it pre-exists.
    #  If tab is given, the function can assume that it has passed the validator.
    @classmethod
    def factory(cls, tab):
        if tab is None:
            pass
        tab_type = tab['type']
        if tab_type not in COURSE_TAB_CLASSES:
            raise InvalidTabsException(
                'Unknown tab type {0}. Known types: {1}'.format(tab_type, COURSE_TAB_CLASSES)
            )

        tab_class = COURSE_TAB_CLASSES[tab['type']]
        tab_class.validate(tab)
        return tab_class(tab=tab)

    def to_json(self):
        return {'type': self.type(), 'name': self.name}

class AuthenticatedCourseTab(CourseTab):
    def can_display(self, course, is_user_authenticated, is_user_staff):
        return is_user_authenticated

class CoursewareTab(CourseTab):
    """
    A tab containing the course content.
    """
    def type(self):
        return 'courseware'

    def __init__(self, tab=None):
        # Translators: 'Courseware' refers to the tab in the courseware that leads to the content of a course
        super(CoursewareTab, self).__init__(
            name=_('Courseware'),
            active_page_name=self.type(),
            link_func=link_reverse_func(self.type()),
        )

class CourseInfoTab(CourseTab):
    """
    A tab containing information about the course.
    """
    def type(self):
        return 'course_info'

    def __init__(self, tab=None):
        # Translators: "Course Info" is the name of the course's information and updates page
        super(CourseInfoTab, self).__init__(
            name=tab['name'] if tab else _('Course Info'),
            active_page_name='info',
            link_func=link_reverse_func('info'),
        )

    @classmethod
    def validate(cls, tab):
        need_name(tab)

class ProgressTab(AuthenticatedCourseTab):
    """
    A tab containing information about the authenticated user's progress.
    """
    def type(self):
        return 'progress'

    def __init__(self, tab=None):
        super(ProgressTab, self).__init__(
            name=tab['name'] if tab else _('Progress'),
            active_page_name=type,
            link_func=link_reverse_func(self.type()),
        )

    def can_display(self, course, is_user_authenticated, is_user_staff):
        return not course.hide_progress_tab

class WikiTab(CourseTab):
    """
    A tab containing the course wiki.
    """
    def type(self):
        return 'wiki'

    def __init__(self, tab=None):
        super(WikiTab, self).__init__(
            name=tab['name'] if tab else _('Wiki'),
            active_page_name=self.type(),
            link_func=link_reverse_func('course_wiki'),
        )

    def can_display(self, course, is_user_authenticated, is_user_staff):
        return settings.WIKI_ENABLED

    @classmethod
    def validate(cls, tab):
        need_name(tab)

class DiscussionTab(CourseTab):
    """
    A tab only for the new Berkeley discussion forums.
    """
    def type(self):
        return 'discussion'

    def __init__(self, tab=None):
        # Translators: "Discussion" is the title of the course forum page
        super(DiscussionTab, self).__init__(
            name=tab['name'] if tab else _('Discussion'),
            active_page_name=self.type(),
            link_func=link_reverse_func('django_comment_client.forum.views.forum_form_discussion'),
        )

    def can_display(self, course, is_user_authenticated, is_user_staff):
        return settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE')

    @classmethod
    def validate(cls, tab):
        need_name(tab)

class LinkTab(CourseTab):
    link_value = ''

    def __init__(self, name, active_page_name, link_value):
        self.link_value = link_value
        super(LinkTab, self).__init__(
            name=name,
            active_page_name=active_page_name,
            link_func=link_value_func(self.link_value),
        )

    def get(self, key, default=None):
        if key == 'link':
            return self.link_value
        else:
            return super(LinkTab, self).get(key)

    def __setitem__(self, key, value):
        if key == 'link':
            self.link_value = value
        else:
            super(LinkTab, self).__setitem__(key, value)

class ExternalDiscussionTab(LinkTab):
    """
    A tab that links to an external discussion service.
    """
    def type(self):
        return 'external_discussion'

    def __init__(self, tab=None, link_value=None):
        link_value = tab['link'] if tab else link_value
        # Translators: 'Discussion' refers to the tab in the courseware that leads to the discussion forums
        super(ExternalDiscussionTab, self).__init__(
            name=_('Discussion'),
            active_page_name='discussion',
            link_value=self.link_value,
        )

    @classmethod
    def validate(cls, tab):
        key_checker(['link'])(tab)

    def to_json(self):
        return {'type': self.type(), 'name': self.name, 'link': self.link_value}

class ExternalLinkTab(LinkTab):
    def type(self):
        return 'external_link'

    def __init__(self, tab):
        super(ExternalLinkTab, self).__init__(
            name=tab['name'],
            active_page_name='',  # External links are never active.
            link_value=tab['link'],
        )

    @classmethod
    def validate(cls, tab):
        key_checker(['name', 'link'])(tab)

class StaticTab(CourseTab):
    url_slug = ''

    def type(self):
        return 'static_tab'

    @classmethod
    def validate(cls, tab):
        key_checker(['name', 'url_slug'])(tab)

    def __init__(self, tab=None, name=None, url_slug=None):
        self.url_slug = tab['url_slug'] if tab else url_slug
        tab_name = tab['name'] if tab else name
        super(StaticTab, self).__init__(
            name=tab_name,
            active_page_name='static_tab_{0}'.format(self.url_slug),
            link_func=lambda course: reverse(self.type(), args=[course.id, self.url_slug]),
        )

    def get(self, key, default=None):
        if key == 'url_slug':
            return self.url_slug
        else:
            return super(StaticTab, self).get(key)

    def __setitem__(self, key, value):
        if key == 'url_slug':
            self.url_slug = value
        else:
            super(StaticTab, self).__setitem__(key, value)

    def get_location(self, course):
        return Location(
            course.location.tag, course.location.org, course.location.course,
            'static_tab',
            self.url_slug
        )

    def to_json(self):
        return {'type': self.type(), 'name': self.name, 'url_slug': self.url_slug}

class TextbookTabsType(AuthenticatedCourseTab):
    def __init__(self, tab=None):
        super(TextbookTabsType, self).__init__('', '', '')

    @abstractmethod
    def books(self, course):
        pass

class TextbookTab(CourseTab):
    pass

class TextbookTabs(TextbookTabsType):
    def type(self):
        return 'textbooks'

    def can_display(self, course, is_user_authenticated, is_user_staff):
        return settings.FEATURES.get('ENABLE_TEXTBOOK')

    def books(self, course):
        for index, textbook in enumerate(course.textbooks):
            yield TextbookTab(
                name=textbook.title,
                active_page_name='textbook/{0}'.format(index),
                link_func=lambda course: reverse('book', args=[course.id, index]),
            )

class PDFTextbookTabs(TextbookTabsType):
    def type(self):
        return 'pdf_textbooks'

    def books(self, course):
        for index, textbook in enumerate(course.pdf_textbooks):
            yield TextbookTab(
                name=textbook['tab_title'],
                active_page_name='pdftextbook/{0}'.format(index),
                link_func=lambda course: reverse('pdf_book', args=[course.id, index]),
            )

class HtmlTextbookTabs(TextbookTabsType):
    def type(self):
        return 'html_textbooks'

    def books(self, course):
        for index, textbook in enumerate(course.html_textbooks):
            yield TextbookTab(
                name=textbook['tab_title'],
                active_page_name='htmltextbook/{0}'.format(index),
                link_func=lambda course: reverse('html_book', args=[course.id, index]),
            )

class GradingTab(object):
    pass

class StaffTab(object):
    def can_display(self, course, is_user_authenticated, is_user_staff):
        return is_user_staff

class StaffGradingTab(CourseTab, GradingTab, StaffTab):
    def type(self):
        return 'staff_grading'

    def __init__(self, tab=None):
        # Translators: "Staff grading" appears on a tab that allows
        # staff to view open-ended problems that require staff grading
        super(StaffGradingTab, self).__init__(
            name=_("Staff grading"),
            active_page_name=self.type(),
            link_func=link_reverse_func(self.type()),
        )

class PeerGradingTab(AuthenticatedCourseTab, GradingTab):
    def type(self):
        return 'peer_grading'

    def __init__(self, tab=None):
        # Translators: "Peer grading" appears on a tab that allows
        # students to view open-ended problems that require grading
        super(PeerGradingTab, self).__init__(
            name=_("Peer grading"),
            active_page_name=self.type(),
            link_func=link_reverse_func(self.type()),
        )

class OpenEndedGradingTab(AuthenticatedCourseTab, GradingTab):
    def type(self):
        return 'open_ended'

    def __init__(self, tab=None):
        # Translators: "Open Ended Panel" appears on a tab that, when clicked, opens up a panel that
        # displays information about open-ended problems that a user has submitted or needs to grade
        super(OpenEndedGradingTab, self).__init__(
            name=_("Open Ended Panel"),
            active_page_name=self.type(),
            link_func=link_reverse_func('open_ended_notifications'),
        )

class SyllabusTab(CourseTab):
    def type(self):
        return 'syllabus'

    def can_display(self, course, is_user_authenticated, is_user_staff):
        return hasattr(course, 'syllabus_present') and course.syllabus_present

    def __init__(self, tab=None):
        super(SyllabusTab, self).__init__(
            name=_('Syllabus'),
            active_page_name=self.type(),
            link_func=link_reverse_func(self.type()),
        )

class NotesTab(AuthenticatedCourseTab):
    def type(self):
        return 'notes'

    def can_display(self, course, is_user_authenticated, is_user_staff):
        return settings.FEATURES.get('ENABLE_STUDENT_NOTES')

    def __init__(self, tab=None):
        super(NotesTab, self).__init__(
            name=tab['name'],
            active_page_name=self.type(),
            link_func=link_reverse_func(self.type()),
        )

class InstructorTab(CourseTab, StaffTab):
    def type(self):
        return 'instructor'

    def __init__(self, tab=None):
        # Translators: 'Instructor' appears on the tab that leads to the instructor dashboard, which is
        # a portal where an instructor can get data and perform various actions on their course
        super(InstructorTab, self).__init__(
            name=_('Instructor'),
            active_page_name=self.type(),
            link_func=link_reverse_func('instructor_dashboard'),
        )

class CourseTabList(List):
    @staticmethod
    def initialize_default(course):

        course.tabs.append(CoursewareTab())
        course.tabs.append(CourseInfoTab())
        course.tabs.append(SyllabusTab())
        course.tabs.append(TextbookTabs())

        # # If they have a discussion link specified, use that even if we feature
        # # flag discussions off. Disabling that is mostly a server safety feature
        # # at this point, and we don't need to worry about external sites.
        if course.discussion_link:
            course.tabs.append(ExternalDiscussionTab(None, course.discussion_link))
        else:
            course.tabs.append(DiscussionTab())

        course.tabs.append(WikiTab())
        course.tabs.append(ProgressTab())

    @staticmethod
    def get_discussion(course):
        for tab in course.tabs:
            if isinstance(tab, DiscussionTab) or isinstance(tab, ExternalDiscussionTab):
                return tab
        return None

    @staticmethod
    def get_tab_by_slug(course, url_slug):
        """
        Look for a tab with the specified 'url_slug'.  Returns the tab or None if not found.
        """
        for tab in course.tabs:
            # The validation code checks that these exist.
            if tab.get('url_slug') == url_slug:
                return tab
        return None

    @staticmethod
    def iterate_displayable(course, is_user_authenticated=True, is_user_staff=True):
        for tab in course.tabs:
            if tab.can_display(course, is_user_authenticated, is_user_staff):
                if isinstance(tab, TextbookTabsType):
                    for book in tab.books(course):
                        yield book
                else:
                    yield tab
        instructor_tab = InstructorTab()
        if instructor_tab.can_display(course, is_user_authenticated, is_user_staff):
            yield instructor_tab

    @classmethod
    def __validate_tabs(cls, tabs):
        """
        Check that the tabs set for the specified course is valid.  If it
        isn't, raise InvalidTabsException with the complaint.

        Specific rules checked:
        - if no tabs specified, that's fine
        - if tabs specified, first two must have type 'courseware' and 'course_info', in that order.
        - All the tabs must have a type in VALID_TAB_TYPES.

        """
        if tabs is None or len(tabs) == 0:
            return

        if len(tabs) < 2:
            raise InvalidTabsException("Expected at least two tabs.  tabs: '{0  }'".format(tabs))

        if tabs[0]['type'] != 'courseware':
            raise InvalidTabsException(
                "Expected first tab to have type 'courseware'.  tabs: '{0}'".format(tabs))

        if tabs[1]['type'] != 'course_info':
            raise InvalidTabsException(
                "Expected second tab to have type 'course_info'.  tabs: '{0}'".format(tabs))

        # Possible other checks: make sure tabs that should only appear once (e.g. courseware)
        # are actually unique (otherwise, will break active tag code)

    def to_json(self, values):
        json_data = []
        if values:
            for val in values:
                if isinstance(val, CourseTab):
                    json_data.append(val.to_json())
                elif isinstance(val, dict):
                    json_data.append(val)
                else:
                    continue
        return json_data

    def from_json(self, values):
        self.__validate_tabs(values)
        tabs = []
        for tab in values:
            tabs.append(CourseTab.factory(tab))
        return tabs

COURSE_TAB_CLASSES = {
    'courseware': CoursewareTab,
    'course_info': CourseInfoTab,
    'wiki': WikiTab,
    'discussion': DiscussionTab,
    'external_discussion': ExternalDiscussionTab,
    'external_link': ExternalLinkTab,
    'textbooks': TextbookTabs,
    'pdf_textbooks': PDFTextbookTabs,
    'html_textbooks': HtmlTextbookTabs,
    'progress': ProgressTab,
    'static_tab': StaticTab,
    'peer_grading': PeerGradingTab,
    'staff_grading': StaffGradingTab,
    'open_ended': OpenEndedGradingTab,
    'notes': NotesTab,
    'syllabus': SyllabusTab,
    'instructor': InstructorTab, # not persisted
}

def link_reverse_func(reverse_name):
    """
    Returns a function that calls the django reverse URL lookup
    """
    return lambda course: reverse(reverse_name, args=[course.id])

def link_value_func(value):
    return lambda course: value

#### Validators
#  A validator takes a dict and raises InvalidTabsException if required
#    fields are missing or otherwise wrong.  (e.g. "is there a 'name' field?).  Validators can assume
#    that the type field is valid.

def key_checker(expected_keys):
    """
    Returns a function that checks that specified keys are present in a dict
    """
    def check(dictionary):
        for key in expected_keys:
            if key not in dictionary:
                raise InvalidTabsException(
                    'Key {0} not present in {1}'.format(key, dictionary)
                )
    return check

need_name = key_checker(['name'])

class InvalidTabsException(Exception):
    """
    A complaint about invalid tabs.
    """
    pass
