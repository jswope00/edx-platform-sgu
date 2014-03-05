"""
Tabs configuration.  By the time the tab is being rendered, it's just a name,
link, and css class (CourseTab tuple).  Tabs are specified in course policy.
Each tab has a type, and possibly some type-specific parameters.

To add a new tab type, add a TabImpl to the VALID_TAB_TYPES dict below--it will
contain a validation function that checks whether config for the tab type is
valid, and a generator function that takes the config, user, and course, and
actually generates the CourseTab.
"""

from collections import namedtuple
import logging

from courseware.access import has_access

from .module_render import get_module
from courseware.access import has_access
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from courseware.model_data import FieldDataCache

from open_ended_grading import open_ended_notifications

log = logging.getLogger(__name__)


CourseTabBase = namedtuple('CourseTab', 'name link is_active has_img img')


def CourseTab(name, link, is_active, has_img=False, img=""):
    return CourseTabBase(name, link, is_active, has_img, img)

def _staff_grading(tab, user, course, request):
    notifications  = open_ended_notifications.staff_grading_notifications(course, user)
    pending_grading = notifications['pending_grading']
    img_path = notifications['img_path']
    return [CourseTab(tab_name, link, "staff_grading", pending_grading, img_path)]

def _peer_grading(tab, user, course, request):
    notifications = open_ended_notifications.peer_grading_notifications(course, user)
    pending_grading = notifications['pending_grading']
    img_path = notifications['img_path']
    return [CourseTab(tab_name, link, "peer_grading", pending_grading, img_path)]


def _combined_open_ended_grading(tab, user, course, request):
    notifications  = open_ended_notifications.combined_notifications(course, user)
    pending_grading = notifications['pending_grading']
    img_path = notifications['img_path']

    return [CourseTab(tab_name, link, "open_ended", pending_grading, img_path)]

def get_course_tabs(user, course, active_page, request):
    """
    Return the tabs to show a particular user, as a list of CourseTab items.
    """

   #NAATODO
    return tabs


def get_discussion_link(course):
    """
    Return the URL for the discussion tab for the given `course`.
    """

    # NAATODO
    pass


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
