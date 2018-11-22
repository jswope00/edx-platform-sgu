from django.core.management.base import BaseCommand, CommandError
from lms.djangoapps.instructor.views.api import students_update_enrollment_modified
from handle_pubh import create_enrollment_list, create_unenrollment_list

class Command(BaseCommand):
    def handle(self, *args, **options):
	course_id = 'course-v1:SGU+SGU101+Ongoing'
	enroll_email_list = create_enrollment_list(course_id)
	unenroll_email_list = create_unenrollment_list(course_id)
	students_update_enrollment_modified(enroll_email_list, course_id, 'enroll')
	students_update_enrollment_modified(unenroll_email_list, course_id, 'unenroll')

        course_id = 'course-v1:SGU+Practicum+OPEN'
	enroll_open_email_list = create_enrollment_list(course_id)
        unenroll_open_email_list = create_unenrollment_list(course_id)
        students_update_enrollment_modified(enroll_open_email_list, course_id, 'enroll')
        students_update_enrollment_modified(unenroll_open_email_list, course_id, 'unenroll')

