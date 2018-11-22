from django.core.management.base import BaseCommand, CommandError
from lms.djangoapps.instructor.views.api import students_update_enrollment_modified
from handle_pubh import create_enrollment_list, create_unenrollment_list

class Command(BaseCommand):
    def handle(self, *args, **options):
	enroll_email_list = create_enrollment_list()
	unenroll_email_list = create_unenrollment_list()
	course_id = 'course-v1:SGU+SGU101+Ongoing'
	students_update_enrollment_modified(enroll_email_list, course_id, 'enroll')
	students_update_enrollment_modified(unenroll_email_list, course_id, 'unenroll')

