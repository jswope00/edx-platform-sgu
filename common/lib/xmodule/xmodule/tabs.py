from collections import namedtuple
from xblock.fields import List
from django.conf import settings
from django.core.urlresolvers import reverse

# NAATODO - is this doing the correct thing?
# We only need to scrape strings for i18n in this file, since ugettext is
# called on them in the template:
# https://github.com/edx/edx-platform/blob/master/lms/templates/courseware/course_navigation.html#L29
_ = lambda text: text

##### Tab class.
class CourseTab(object):
    def __init__(self, type, link, active_page_name):
        self.type = type
        self.link = link
        self.active_page_name = active_page_name

    #####  Factory methods for various Tabs
    @classmethod
    def _courseware(cls, course, lms):
        """
        This returns a tab containing the course content.
        """
        link = reverse('courseware', args=[course.id])
        # Translators: 'Courseware' refers to the tab in the courseware that leads to the content of a course
        return [CourseTab(_('Courseware'), link, "courseware")]

    @classmethod
    def _course_info(cls, course, tab):
        """
        This returns a tab containing information about the course.
        """
        link = reverse('info', args=[course.id])
        return [CourseTab(tab['name'], link, "info")]

    @classmethod
    def _progress(cls, course, tab, include_authenticated_tabs):
        """
        This returns a tab containing information about the authenticated user's progress.
        """
        if include_authenticated_tabs:
            link = reverse('progress', args=[course.id])
            return [CourseTab(tab['name'], link, "progress")]
        return []

    @classmethod
    def _wiki(cls, course, tab):
        """
        This returns a tab containing the course wiki.
        """
        if settings.WIKI_ENABLED:
            link = reverse('course_wiki', args=[course.id])
            return [CourseTab(tab['name'], link, 'wiki')]
        return []

    @classmethod
    def _discussion(cls, course, tab):
        """
        This tab format only supports the new Berkeley discussion forums.
        """
        if settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
            link = reverse(
                'django_comment_client.forum.views.forum_form_discussion',
                args=[course.id]
            )
            return [CourseTab(tab['name'], link, 'discussion')]
        return []

    @classmethod
    def _external_discussion(cls, tab):
        """
        This returns a tab that links to an external discussion service
        """
        # Translators: 'Discussion' refers to the tab in the courseware that leads to the discussion forums
        return [CourseTab(_('Discussion'), tab['link'], 'discussion')]

    @classmethod
    def _external_link(cls, tab):
        # external links are never active
        return [CourseTab(tab['name'], tab['link'], False)]

    @classmethod
    def _static_tab(cls, course, tab):
        link = reverse('static_tab', args=[course.id, tab['url_slug']])
        active_str = 'static_tab_{0}'.format(tab['url_slug'])
        return [CourseTab(tab['name'], link, active_str)]

    @classmethod
    def _textbooks(cls, course, include_authenticated_tabs):
        """
        Generates one tab per textbook.  Only displays if user is authenticated.
        """
        if include_authenticated_tabs and settings.FEATURES.get('ENABLE_TEXTBOOK'):
            # since there can be more than one textbook, active_page is e.g. "book/0".
            return [
                CourseTab(
                    textbook.title,
                    reverse('book', args=[course.id, index]),
                    "textbook/{0}".format(index)
                )
                for index, textbook in enumerate(course.textbooks)]
        return []

    @classmethod
    def _pdf_textbooks(cls, course, include_authenticated_tabs):
        """
        Generates one tab per textbook.  Only displays if user is authenticated.
        """
        if include_authenticated_tabs:
            # since there can be more than one textbook, active_page is e.g. "book/0".
            return [
                CourseTab(
                    textbook['tab_title'],
                    reverse('pdf_book', args=[course.id, index]),
                    "pdftextbook/{0}".format(index)
                )
                for index, textbook in enumerate(course.pdf_textbooks)]
        return []

    @classmethod
    def _html_textbooks(cls, course, include_authenticated_tabs):
        """
        Generates one tab per textbook.  Only displays if user is authenticated.
        """
        if include_authenticated_tabs:
            # since there can be more than one textbook, active_page is e.g. "book/0".
            return [
                CourseTab(
                    textbook['tab_title'],
                    reverse('html_book', args=[course.id, index]),
                    "htmltextbook/{0}".format(index)
                )
                for index, textbook in enumerate(course.html_textbooks)]
        return []

    @classmethod
    def _staff_grading(cls, course):
        link = reverse('staff_grading', args=[course.id])

        # Translators: "Staff grading" appears on a tab that allows
        # staff to view open-ended problems that require staff grading
        return [CourseTab(_("Staff grading"), link, "staff_grading")]

    @classmethod
    def _peer_grading(cls, course, include_authenticated_tabs):
        if include_authenticated_tabs:
            link = reverse('peer_grading', args=[course.id])

            # Translators: "Peer grading" appears on a tab that allows
            # students to view open-ended problems that require grading
            return [CourseTab(_("Peer grading"), link, "peer_grading")]
        return []

    @classmethod
    def _combined_open_ended_grading(cls, course, include_authenticated_tabs):
        if include_authenticated_tabs:
            link = reverse('open_ended_notifications', args=[course.id])

            # Translators: "Open Ended Panel" appears on a tab that, when clicked, opens up a panel that
            # displays information about open-ended problems that a user has submitted or needs to grade
            return [CourseTab(_("Open Ended Panel"), link, "open_ended")]
        return []

    @classmethod
    def _syllabus(cls, course):
        link = reverse('syllabus', args=[course.id])
        return [CourseTab(_('Syllabus'), link, 'syllabus')]

    @classmethod
    def _notes_tab(cls, course, tab, include_authenticated_tabs):
        if include_authenticated_tabs and settings.FEATURES.get('ENABLE_STUDENT_NOTES'):
            link = reverse('notes', args=[course.id])
            return [CourseTab(tab['name'], link, 'notes')]
        return []

    @classmethod
    def _instructor(cls, course):
        link = reverse('instructor_dashboard', args=[course.id])
        # Translators: 'Instructor' appears on the tab that leads to the instructor dashboard, which is
        # a portal where an instructor can get data and perform various actions on their course
        return CourseTab(_('Instructor'), link, 'instructor')

    def __link__(self, ):



class CourseTabList(List):
    @classmethod
    def default_for_course(cls, course, include_authenticated_tabs, include_staff_tabs):
        """
        Return the default set of tabs.
        The reason this exists is because of the life cycle of this object.
        Otherwise, it could have been in the __init__ function.
        """

        # NAATODO - is it correct to add tabs through values ?

        tab_list = []
        tab_list.extend(CourseTab._courseware(course))
        tab_list.extend(CourseTab._course_info({'name': 'Course Info'}, course))

        if hasattr(course, 'syllabus_present') and course.syllabus_present:
            tab_list.append(CourseTab._syllabus(course))

        tab_list.extend(CourseTab._textbooks(course, include_authenticated_tabs))

        discussion_link = get_discussion_link(course)
        if discussion_link:
            tab_list.append(CourseTab('Discussion', discussion_link))

        tab_list.extend(CourseTab._wiki({'name': 'Wiki', 'type': 'wiki'}, course))

        if not course.hide_progress_tab:
            tab_list.extend(CourseTab._progress({'name': 'Progress'}, course, include_authenticated_tabs))

        if include_staff_tabs:
            tab_list.append(CourseTab._instructor(course))

        return tab_list

    @classmethod
    def from_course(cls, course, include_authenticated_tabs, include_staff_tabs):
        """
        Return the tabs to show a particular user, as a list of CourseTab items.
        """
        if not hasattr(course, 'tabs') or not course.tabs:
            return cls.default_for_course(course, include_authenticated_tabs, include_staff_tabs)

        # validate the tabs
        cls.__validate_tabs(course)

        tab_list = []
        course_tabs = course.tabs
        for tab in course_tabs:
            # expect handlers to return lists--handles things that are turned off
            # via feature flags, and things like 'textbook' which might generate
            # multiple tabs.
            factory_method = VALID_TAB_TYPES[tab['type']].factory
            tab_list.extend(factory_method(course, tab, include_authenticated_tabs))

        # Instructor tab is special--automatically added if user is staff for the course
        if include_staff_tabs:
            tab_list.append(CourseTab._instructor(course))
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
            raise InvalidTabsException("Expected at least two tabs.  tabs: '{0}'".format(tabs))

        if tabs[0]['type'] != 'courseware':
            raise InvalidTabsException(
                "Expected first tab to have type 'courseware'.  tabs: '{0}'".format(tabs))

        if tabs[1]['type'] != 'course_info':
            raise InvalidTabsException(
                "Expected second tab to have type 'course_info'.  tabs: '{0}'".format(tabs))

        for t in tabs:
            if t['type'] not in VALID_TAB_TYPES:
                raise InvalidTabsException("Unknown tab type {0}. Known types: {1}"
                                           .format(t['type'], VALID_TAB_TYPES))
            # the type-specific validator checks the rest of the tab config
            VALID_TAB_TYPES[t['type']].validator(t)

        # Possible other checks: make sure tabs that should only appear once (e.g. courseware)
        # are actually unique (otherwise, will break active tag code)


# NAATODO - should this be defined within the CourseTab discussion method?
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
            return tab

    return None
        
class InvalidTabsException(Exception):
    """
    A complaint about invalid tabs.
    """
    pass

#### Validators
def key_checker(expected_keys):
    """
    Returns a function that checks that specified keys are present in a dict
    """
    def check(dictionary):
        for key in expected_keys:
            if key not in dictionary:
                raise InvalidTabsException(
                    "Key {0} not present in {1}".format(key, dictionary)
                )
    return check

need_name = key_checker(['name'])

def null_validator(d):
    """
    Don't check anything--use for tabs that don't need any params. (e.g. textbook)
    """
    pass

# encapsulate implementation for a tab:
#  - a validator function: takes the config dict and raises InvalidTabsException if required
#    fields are missing or otherwise wrong.  (e.g. "is there a 'name' field?).  Validators can assume
#    that the type field is valid.
#
#  - a factory function: that takes a course, a tab, a boolean for whether to include authenticated tabs,
#    and return a list of CourseTabs.  The function can assume that it is only called with configs of the
#    appropriate type that have passed the corresponding validator.
TabImpl = namedtuple('TabImpl', 'validator factory')

##### The main tab config dict.

# type -> TabImpl
VALID_TAB_TYPES = {
    'courseware': TabImpl(null_validator, lambda c, t, a: CourseTab._courseware(c)),
    'course_info': TabImpl(need_name, lambda c, t, a: CourseTab._course_info(c, t)),
    'wiki': TabImpl(need_name, lambda c, t, a: CourseTab._wiki(c, t)),
    'discussion': TabImpl(need_name, lambda c, t, a: CourseTab._discussion(c, t)),
    'external_discussion': TabImpl(key_checker(['link']), lambda c, t, a: CourseTab._external_discussion(t)),
    'external_link': TabImpl(key_checker(['name', 'link']), lambda c, t, a: CourseTab._external_link(t)),
    'textbooks': TabImpl(null_validator, lambda c, t, a: CourseTab._textbooks(c, a)),
    'pdf_textbooks': TabImpl(null_validator, lambda c, t, a: CourseTab._pdf_textbooks(c, a)),
    'html_textbooks': TabImpl(null_validator, lambda c, t, a: CourseTab._html_textbooks(c, a)),
    'progress': TabImpl(need_name, lambda c, t, a: CourseTab._progress(c, t, a)),
    'static_tab': TabImpl(key_checker(['name', 'url_slug']), lambda c, t, a: CourseTab._static_tab(c, t)),
    'peer_grading': TabImpl(null_validator, lambda c, t, a: CourseTab._peer_grading(c, a)),
    'staff_grading': TabImpl(null_validator, lambda c, t, a: CourseTab._staff_grading(c)),
    'open_ended': TabImpl(null_validator, lambda c, t, a: CourseTab._combined_open_ended_grading(c, a)),
    'notes': TabImpl(null_validator, lambda c, t, a: CourseTab._notes_tab(c, t, a)),
    'syllabus': TabImpl(null_validator, lambda c, t, a: CourseTab._syllabus(c))
}
