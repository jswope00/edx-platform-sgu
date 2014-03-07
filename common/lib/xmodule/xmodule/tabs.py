from collections import namedtuple
from xblock.fields import List
from django.conf import settings
from django.core.urlresolvers import reverse

from abc import ABCMeta, abstractmethod, abstractproperty

# NAATODO - is this doing the correct thing?
# We only need to scrape strings for i18n in this file, since ugettext is
# called on them in the template:
# https://github.com/edx/edx-platform/blob/master/lms/templates/courseware/course_navigation.html#L29
_ = lambda text: text


##### Tab class.
class CourseTab(object):
    __metaclass__ = ABCMeta

    def __init__(self, name, active_page_name, link_func = None):
        # name of the tab - may or may not be stored in the database
        self.name = name

        # used by UI layers to indicate which tab is active
        self.active_page_name = active_page_name

        # function that computes the link for the tab
        self.link_func = link_func

    @classmethod
    def validate(cls, tab):
        """
        Can be overridden by sub-classes that require params in the tab.
        """
        pass

    @abstractproperty
    def type_name(self): pass

    #  A factory function that takes a course and an optional tab if it pre-exists.
    #  If tab is given, the function can assume that it has passed the validator.
    @classmethod
    def factory(cls, course, tab, include_authenticated_tabs):
        tab_type_name = tab['type']
        if tab_type_name not in COURSE_TAB_CLASSES:
            raise InvalidTabsException(
                'Unknown tab type {0}. Known types: {1}'.format(tab_type_name, COURSE_TAB_CLASSES)
            )

        tab_class = COURSE_TAB_CLASSES[tab['type']]
        if tab_class is AuthenticatedCourseTab and include_authenticated_tabs is False:
            return None
        tab_class.validate(tab)
        return tab_class.create(course, tab)

    def to_json(self):
        return {'type': self.type_name, 'name': self.name}

class AuthenticatedCourseTab(CourseTab):
    pass

class CoursewareTab(CourseTab):
    """
    A tab containing the course content.
    """
    def type_name(self): return 'courseware'

    @classmethod
    def create(cls, course, tab=None):
        # Translators: 'Courseware' refers to the tab in the courseware that leads to the content of a course
        return [
            cls(
                name=_('Courseware'),
                active_page_name=cls.type_name,
                link_func=link_reverse(cls.type_name, course),
            )]

class CourseInfoTab(CourseTab):
    """
    A tab containing information about the course.
    """
    def type_name(self): return 'course_info'

    @classmethod
    def validate(cls, tab):
        need_name(tab)

    @classmethod
    def create(cls, course, tab=None):
        # Translators: 'Courseware' refers to the tab in the courseware that leads to the content of a course
        if tab:
            tab_name=tab['name']
        else:
            tab_name = 'Course Info'
        return [
            cls(
                name=tab_name,
                active_page_name='info',
                link_func=link_reverse('info', course),
            )]

class ProgressTab(AuthenticatedCourseTab):
    """
    A tab containing information about the authenticated user's progress.
    """

    def type_name(self): return 'progress'

    @classmethod
    def create(cls, course, tab=None):
        if not course.hide_progress_tab:
            if tab:
                tab_name=tab['name']
            else:
                tab_name = 'Progress'
            return [
                cls(
                    name=tab_name,
                    active_page_name=cls.type_name,
                    link_func=link_reverse(cls.type_name, course),
                )]
        return []

class WikiTab(CourseTab):
    """
    A tab containing the course wiki.
    """
    def type_name(self): return 'wiki'

    @classmethod
    def validate(cls, tab):
        need_name(tab)

    @classmethod
    def create(cls, course, tab=None):
        if settings.WIKI_ENABLED:
            if tab:
                tab_name=tab['name']
            else:
                tab_name = 'Wiki'
            return [
                cls(
                    name=tab_name,
                    active_page_name=cls.type_name,
                    link_func=link_reverse('course_wiki', course),
                )]
        return []

class DiscussionTab(CourseTab):
    """
    A tab only for the new Berkeley discussion forums.
    """
    def type_name(self): return 'discussion'

    @classmethod
    def validate(cls, tab):
        need_name(tab)

    @classmethod
    def create(cls, course, tab=None):
        if settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
            return [
                cls(
                    name=tab['name'],
                    active_page_name=cls.type_name,
                    link_func=link_reverse('django_comment_client.forum.views.forum_form_discussion', course),
                )]
        return []

class ExternalDiscussionTab(CourseTab):
    """
    A tab that links to an external discussion service.
    """
    def type_name(self): return 'external_discussion'

    @classmethod
    def validate(cls, tab):
        key_checker(['link'])(tab)

    @classmethod
    def create(cls, course, tab):
        # Translators: 'Discussion' refers to the tab in the courseware that leads to the discussion forums
        return [
            cls(
                name=_('Discussion'),
                active_page_name='discussion',
                link_func=link_value(tab['link']),
            )]

class ExternalLinkTab(CourseTab):
    def type_name(self): return 'external_link'

    @classmethod
    def validate(cls, tab):
        key_checker(['name', 'link'])(tab)

    @classmethod
    def create(cls, course, tab):
        return [
            cls(
                name=tab['name'],
                active_page_name='',  # External links are never active.
                link_func=link_value(tab['link']),
            )]

class StaticTab(CourseTab):
    def type_name(self): return 'static_tab'

    url_slug = ''

    @classmethod
    def validate(cls, tab):
        key_checker(['name', 'url_slug'])(tab)

    @classmethod
    def create(cls, course, tab):
        static_tab = cls(
            name=tab['name'],
            active_page_name='static_tab_{0}'.format(tab['url_slug']),
            link_func=lambda: reverse(cls.type_name, args=[course.id, tab['url_slug']]),
            )
        static_tab.url_slug = tab['url_slug']
        return [static_tab]

class TextbookTabs(AuthenticatedCourseTab):
    def type_name(self): return 'textbooks'

    @classmethod
    def create(cls, course, tab=None):
        if settings.FEATURES.get('ENABLE_TEXTBOOK'):
            return [
                cls(
                    name=textbook.title,
                    active_page_name='textbook/{0}'.format(index),
                    link_func=lambda: reverse('book', args=[course.id, index]),
                )
                for index, textbook in enumerate(course.textbooks)]
            return []

class PDFTextbookTabs(AuthenticatedCourseTab):
    def type_name(self): return 'pdf_textbooks'

    @classmethod
    def create(cls, course, tab):
        return [
            cls(
                name=textbook['tab_title'],
                active_page_name='pdftextbook/{0}'.format(index),
                link_func=lambda: reverse('pdf_book', args=[course.id, index]),
            )
            for index, textbook in enumerate(course.pdf_textbooks)]
        return []

class HtmlTextbookTabs(AuthenticatedCourseTab):
    def type_name(self): return 'html_textbooks'

    @classmethod
    def create(cls, course, tab):
        return [
            cls(
                name=textbook['tab_title'],
                active_page_name='htmltextbook/{0}'.format(index),
                link_func=lambda: reverse('html_book', args=[course.id, index]),
            )
            for index, textbook in enumerate(course.html_textbooks)]
        return []

class StaffGradingTab(CourseTab):
    def type_name(self): return 'staff_grading'

    @classmethod
    def create(cls, course, tab):
        # Translators: "Staff grading" appears on a tab that allows
        # staff to view open-ended problems that require staff grading
        return [
            cls(
                name=_("Staff grading"),
                active_page_name=cls.type_name,
                link_func=link_reverse(cls.type_name, course),
            )]

class PeerGradingTab(AuthenticatedCourseTab):
    def type_name(self): return 'peer_grading'

    @classmethod
    def create(cls, course, tab):
        # Translators: "Peer grading" appears on a tab that allows
        # students to view open-ended problems that require grading
        return [
            cls(
                name=_("Peer grading"),
                active_page_name=cls.type_name,
                link_func=link_reverse(cls.type_name, course),
            )]

class OpenEndedGradingTab(AuthenticatedCourseTab):
    def type_name(self): return 'open_ended'

    @classmethod
    def create(cls, course, tab):
        # Translators: "Open Ended Panel" appears on a tab that, when clicked, opens up a panel that
        # displays information about open-ended problems that a user has submitted or needs to grade
        return [
            cls(
                name=_("Open Ended Panel"),
                active_page_name=cls.type_name,
                link_func=link_reverse('open_ended_notifications', course),
            )]

class SyllabusTab(CourseTab):
    def type_name(self): return 'syllabus'

    @classmethod
    def create(cls, course, tab=None):
        if hasattr(course, 'syllabus_present') and course.syllabus_present:
            return [
                cls(
                    name=_('Syllabus'),
                    active_page_name=cls.type_name,
                    link_func=link_reverse(cls.type_name, course),
                )]
        return []

class NotesTab(AuthenticatedCourseTab):
    def type_name(self): return 'notes'

    @classmethod
    def create(cls, course, tab):
        if settings.FEATURES.get('ENABLE_STUDENT_NOTES'):
            return [
                cls(
                    name=tab['name'],
                    active_page_name=cls.type_name,
                    link_func=link_reverse(cls.type_name, course),
                )]
        return []

class InstructorTab(CourseTab):
    def type_name(self): return 'instructor'

    @classmethod
    def create(cls, course, tab=None):
        # Translators: 'Instructor' appears on the tab that leads to the instructor dashboard, which is
        # a portal where an instructor can get data and perform various actions on their course
        return [
            cls(
                name=_('Instructor'),
                active_page_name=cls.type_name,
                link_func=link_reverse('instructor_dashboard', course),
            )]

class CourseTabList(List):
    def initialize_defaults(self, course, include_authenticated_tabs, include_staff_tabs):

        self.extend(CoursewareTab.create(course))
        self.extend(CourseInfoTab.create(course))
        self.extend(SyllabusTab.create(course))

        if include_authenticated_tabs:
            self.extend(TextbookTabs.create(course))

        discussion_link = CourseTabList.get_discussion_link(course)
        if discussion_link:
            self.extend(DiscussionTab.create(discussion_link)) # NAATODO

        self.extend(WikiTab.create(course))

        if include_authenticated_tabs:
            self.extend(ProgressTab.create(course))

        if include_staff_tabs:
            self.extend(InstructorTab.create(course))

    @classmethod
    def from_course(cls, course, include_authenticated_tabs, include_staff_tabs):
        """
        Return the tabs to show a particular user, as a list of CourseTab items.
        """
        if not hasattr(course, 'tabs') or not course.tabs:
            new_tab_list = CourseTabList()
            new_tab_list.initialize_defaults(course, include_authenticated_tabs, include_staff_tabs)
            return new_tab_list

        # validate the tabs
        cls.__validate_tabs(course)

        tab_list = []
        for tab in course.tabs:
            # expect handlers to return lists--handles things that are turned off
            # via feature flags, and things like 'textbook' which might generate multiple tabs.
            tab_list.extend(CourseTab.factory(course, tab, include_authenticated_tabs))

        # Instructor tab is special--automatically added if user is staff for the course
        if include_staff_tabs:
            tab_list.extend(InstructorTab.create(course))

        return tab_list

    @classmethod
    def __validate_tabs(cls, course):
        """
        Check that the tabs set for the specified course is valid.  If it
        isn't, raise InvalidTabsException with the complaint.

        Specific rules checked:
        - if no tabs specified, that's fine
        - if tabs specified, first two must have type 'courseware' and 'course_info', in that order.
        - All the tabs must have a type in VALID_TAB_TYPES.

        """
        tabs = course.tabs
        if tabs is None:
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

    @staticmethod
    def get_static_tab_by_slug(course, tab_slug):
        """
        Look for a tab with type 'static_tab' and the specified 'tab_slug'.  Returns
        the tab (a config dict), or None if not found.
        """
        if course.tabs is None:
            return None
        for tab in course.tabs:
            # The validation code checks that these exist.
            if tab['type'] == 'static_tab' and tab['url_slug'] == tab_slug:
                return StaticTab.create(course, tab)

        return None

    @staticmethod
    def get_static_tab_contents(request, course, tab):
        loc = Location(course.location.tag, course.location.org, course.location.course, 'static_tab', tab['url_slug'])
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(course.id,
            request.user, modulestore().get_instance(course.id, loc), depth=0)
        tab_module = get_module(request.user, request, loc, field_data_cache, course.id,
                                static_asset_path=course.static_asset_path)

        logging.debug('course_module = {0}'.format(tab_module))

        html = ''

        if tab_module is not None:
            html = tab_module.render('student_view').content

        return html

    @staticmethod
    def get_discussion_link(course):
        """
        Return the URL for the discussion tab for the given `course`.

        If they have a discussion link specified, use that even if we disable
        discussions. Disabling discussions is mostly a server safety feature at
        this point, and we don't need to worry about external sites. Otherwise,
        if the course has a discussion tab or uses the default tabs, return the
        discussion view URL. Otherwise, return None to indicate the lack of a
        discussion tab.
        """
        if course.discussion_link:
            return course.discussion_link
        elif not settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
            return None
        elif hasattr(course, 'tabs') and course.tabs and not any([tab['type'] == 'discussion' for tab in course.tabs]):
            return None
        else:
            return reverse('django_comment_client.forum.views.forum_form_discussion', args=[course.id])

    def to_json(self, values):
        json_data = []
        for val in values:
            if isinstance(val, CourseTab):
                json_data.extend(val.to_json())
            elif isinstance(val, tuple):
                json_data.append(val)
            else:
                continue
        return json_data


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
    'syllabus': SyllabusTab
}

def link_reverse(reverse_name, course):
    """
    Returns a function that calls the django reverse URL lookup
    """
    return lambda: reverse(reverse_name, args=[course.id])

def link_value(value):
    return lambda: value

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
