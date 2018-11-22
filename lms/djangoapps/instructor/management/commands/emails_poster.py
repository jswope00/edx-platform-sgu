from django.core.management.base import BaseCommand, CommandError
from lms.djangoapps.instructor.views.api import students_update_enrollment_modified
from csv_reader_users import update_users_table
from csv_reader_members import update_members_table
from csv_reader_members import create_enrollment_list
from csv_reader_members import create_unenrollment_list

class Command(BaseCommand):
    def handle(self, *args, **options):
        update_users_table()
        update_members_table()
        enrollObject = create_enrollment_list()
        unenrollObject = create_unenrollment_list()

        for each in enrollObject:
            courseID = each[0]
            eList = each[1]
            enroll = 'enroll'
            students_update_enrollment_modified(eList, courseID, enroll)

        for each in unenrollObject:
            courseID = each[0]
            eList = each[1]
            unenroll = 'unenroll'
            students_update_enrollment_modified(eList, courseID, unenroll)
