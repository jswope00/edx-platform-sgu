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

from .module_render import get_module
from xmodule.modulestore.django import modulestore
from xmodule.tabs import InstructorTab, StaffGradingTab, PeerGradingTab, OpenEndedGradingTab, CourseTabList
from courseware.access import has_access
from courseware.model_data import FieldDataCache
from open_ended_grading import open_ended_notifications

log = logging.getLogger(__name__)

def image_for_tab(course_tab, user, course):
    if isinstance(course_tab, StaffGradingTab):
        notifications = open_ended_notifications.staff_grading_notifications(course, user)
    elif isinstance(course_tab, PeerGradingTab):
        notifications = open_ended_notifications.peer_grading_notifications(course, user)
    elif isinstance(course_tab, OpenEndedGradingTab):
        notifications = open_ended_notifications.combined_notifications(course, user)
    else:
        notifications = None

    if notifications and notifications['pending_grading']:
        return notifications['img_path']
    return None

def get_static_tab_contents(request, course, static_tab):
    loc = static_tab.get_location(course)
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(course.id,
        request.user, modulestore().get_instance(course.id, loc), depth=0)
    tab_module = get_module(request.user, request, loc, field_data_cache, course.id,
                            static_asset_path=course.static_asset_path)

    logging.debug('course_module = {0}'.format(tab_module))

    html = ''

    if tab_module is not None:
        html = tab_module.render('student_view').content

    return html
