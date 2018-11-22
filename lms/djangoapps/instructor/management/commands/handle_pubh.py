import MySQLdb
from django.contrib.auth.models import User
from django.db import connection

def get_active_pubh_users(course_id):
    cur = connection.cursor()
    newEnrollmentList = []
    matching_string = "PUBH"
    is_active = 1
    try:
        query = ("select DISTINCT user_id from student_courseenrollment where course_id LIKE '%{0}%' AND is_active='{1}'").format(matching_string,is_active)
        cur.execute(query)
        newEnrollmentList = cur.fetchall()
        newEnrollmentList = [unicode(a[0]) for a in newEnrollmentList]
    except Exception, e:
	print "Something went wrong while filtering PUBH courses active enrollments!"
	print e
    return newEnrollmentList

def get_ongoing_course_enrollments(course_id):
    cur = connection.cursor()
    existingEnrollmentList = []
    is_active = 1
    try:
	query = ("select user_id from student_courseenrollment where course_id='{0}' AND is_active='{1}'").format(course_id, is_active)
        cur.execute(query)
        existingEnrollmentList = cur.fetchall()
        existingEnrollmentList = [unicode(elem[0]) for elem in existingEnrollmentList]
    except Exception, e:
        print "Something went wrong while retrieving existing ONGOING course enrollments!"
	print e
    return existingEnrollmentList

def create_enrollment_list(course_id):
    newEnrollmentList = get_active_pubh_users(course_id)
    existingEnrollmentList = get_ongoing_course_enrollments(course_id)
    user_email_list = []
    try:
        for new_user_id in newEnrollmentList:
            if new_user_id not in existingEnrollmentList:
	        user_email_list.append(User.objects.get(id=new_user_id).email)
    except Exception, e:
	print "Something went wrong while creating enrollment list!"
	print e
    return user_email_list

def create_unenrollment_list(course_id):
    newEnrollmentList = get_active_pubh_users(course_id)
    existingEnrollmentList = get_ongoing_course_enrollments(course_id)
    user_email_list = []
    try:
        for existing_user_id in existingEnrollmentList:
            if existing_user_id not in newEnrollmentList:
                user_email_list.append(User.objects.get(id=existing_user_id).email)
    except Exception, e:
        print "Something went wrong while creating unenrollment list!"
        print e
    return user_email_list

