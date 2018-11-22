import csv
import sys
import MySQLdb
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_with_access, get_course_by_id
from django.contrib.auth.models import User
from student.models import CourseAccessRole
#from instructor.offline_gradecalc import student_grades
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from datetime import datetime
from itertools import chain

from django.db import connection

cur = connection.cursor()

def update_members_table():

        members_csv = open("/home/ubuntu/SGU_Banner/members.csv", 'r')
        cur = connection.cursor()
	update_sgux_id()
        preMembers = []
        newMembers = []
        userPresent = None

        try:
            count = None
            reader = csv.reader(members_csv)
            for row in reader:
                if row == []:
                    pass
                else:
		    #This is only for matching if the course exists against the course_id of members.csv
                    query = ("select * from course_overviews_courseoverview WHERE id LIKE '%{0}%'").format(row[1])
		    count = cur.execute(query)
		    #If course_id matches then the exact row of members.csv will append in newMembers
                    if count > 0:
                        newMembers.append(row)
        except Exception,e:
            print e
        finally:
            members_csv.close()

        try:
            alert = cur.execute("select * from sgu_members")
            if(alert <= 1):
                for new in newMembers:
                    email = new[0]+"@sgu.edu"
                    cur.execute("""INSERT INTO sgu_members(username, email, course_id, type, status) VALUES(%s, %s, %s, %s, %s)""", (new[0],email,new[1],new[2],new[3]))

        except Exception,e:
	    print "check 1 ================ check 1"
            print e
        finally:
            members_csv.close()
                
        try:
            query = "select * from sgu_members"
            cur.execute(query)
            preMembers = cur.fetchall()
            preMembers = [list(elem) for elem in preMembers]
            #Checking every member of present Database with new members.csv received
            for pre in preMembers:
                if pre:
                    sUPre = pre[1]
                    sCPre = pre[3]
                    Check = False
                    #this for loop is for every member in new members.csv
                    for new in newMembers:
                        if new:
                            #if newList member and its course ID equals to any instance in present database
                            if (new[0] == sUPre and new[1] == sCPre):
                                Check = True
                                sUStatusP = pre[5]
                                sUStatusN = new[3]
                                if sUStatusP == sUStatusN:
                                    break
                                else:
                                    if sUStatusN.lower() == 'false':
					#RECORD FOUND TO BE UNENROLL MEANS STATUS IS FALSE NOW
                                        query = ("UPDATE sgu_members SET status='FALSE' Where username='{0}' AND course_id='{1}'").format(pre[1], pre[3])
                                        cur.execute(query)
                                        break
                                    else:
                                        #"RECORD FOUND TO BE ENROLL MEANS STATUS IS TRUE NOW"
                                        query = ("UPDATE sgu_members SET status='TRUE' Where username='{0}' AND course_id='{1}'").format(pre[1], pre[3])
                                        cur.execute(query)
                                        break
                    if Check == False:
                        #"RECORD FOUND TO BE UNENROLL MEANS STATUS IS FALSE NOW, RECORD NOT FOUND IN CSV"
                        query = ("UPDATE sgu_members SET status='FALSE' Where username='{0}' AND course_id='{1}'").format(pre[1], pre[3])
                        cur.execute(query)
            for new in newMembers:
                if new == []:
                    pass
                else:
                    sUNew = new[0]
                    sCNew = new[1]
                    for pre in preMembers:
                        if pre == []:
                            pass
                        else:
                            if (pre[1] == sUNew and pre[3] == sCNew):
                                #"NO NEW RECORD FOUND TO ADD IN TABLE"
                                userPresent = 1
                                break
                            else:
                                userPresent = 0
                    if userPresent == 0:
                    #"NEW MEMBER FOUND TO BE ADD IN TABLE"
                        email = new[0]+"@sgu.edu"
			sgux_id = generate_sgux_id(sCNew)  #sCNew=new[1]=course_id in members.csv
                        cur.execute("""INSERT INTO sgu_members(username, email, course_id, type, status, `sgux-id`) VALUES(%s, %s, %s, %s, %s, %s)""", (new[0],email,new[1],new[2],new[3],sgux_id))
        except Exception,e:
	    print "exception inserting"
            print e
        finally:
            members_csv.close()

def create_enrollment_list():
        courseList = []
        eRequestObject = []
        members_csv = open("/home/ubuntu/SGU_Banner/members.csv", 'r')

        cur = connection.cursor()

        # you must create a Cursor object. It will let
        #  you execute all the queries you need
        try:
            #query = ("SELECT DISTINCT course_id FROM sgu_members")
            query = ("SELECT DISTINCT `sgux-id` FROM sgu_members")
            count = cur.execute(query)
            courseList = cur.fetchall()
            courseList = [list(elem) for elem in courseList]
            for index in courseList:
                statusT = "TRUE"
                type = "student"
                if index == []:
                    pass
                else:
                    eList = []
                    rObject = []
                    #query = ("select email from sgu_members WHERE course_id = '{0}' AND status = '{1}' AND type = '{2}'").format(index[0],statusT,type)
		    query = ("select email from sgu_members WHERE `sgux-id` = '{0}' AND status = '{1}' AND type = '{2}'").format(index[0],statusT,type)
		    cur.execute(query)
                    eList = cur.fetchall()
                    eList = [list(elem) for elem in eList]
                    emailsList = [unicode(a[0]) for a in eList]
                    query = ("select * from course_overviews_courseoverview WHERE id LIKE '%{0}%'").format(index[0])
                    cur.execute(query)
                    courseID = cur.fetchall()
                    courseID = courseID[0][0]
                    #courseID = unicode(courseID, "utf-8")
                    rObject.append(courseID)
                    rObject.append(emailsList)
                    eRequestObject.append(rObject)
        except Exception,e:
            print "exception enrollment",e
        finally:
            members_csv.close()

        return eRequestObject

def create_unenrollment_list():
        courseList = []
        eRequestObject = []
        members_csv = open("/home/ubuntu/SGU_Banner/members.csv", 'r')
        cur = connection.cursor()

        # you must create a Cursor object. It will let
        #  you execute all the queries you need
        try:
            #query = ("SELECT DISTINCT course_id FROM sgu_members")
	    query = ("SELECT DISTINCT `sgux-id` FROM sgu_members")
            count = cur.execute(query)
            courseList = cur.fetchall()
            courseList = [list(elem) for elem in courseList]
            for index in courseList:
                statusF = "FALSE"
                type = "student"
                if index == []:
                    pass
                else:
                    eList = []
                    rObject = []
                    #query = ("select email from sgu_members WHERE course_id = '{0}' AND status = '{1}' AND type = '{2}'").format(index[0],statusF,type)
		    query = ("select email from sgu_members WHERE `sgux-id` = '{0}' AND status = '{1}' AND type = '{2}'").format(index[0],statusF,type)
                    cur.execute(query)
                    eList = cur.fetchall()
                    eList = [list(elem) for elem in eList]
                    emailsList = [unicode(a[0]) for a in eList]
                    query = ("select * from course_overviews_courseoverview WHERE id LIKE '%{0}%'").format(index[0])
                    cur.execute(query)
                    courseID = cur.fetchall()
                    courseID = courseID[0][0]
                    #courseID = unicode(courseID, "utf-8")
                    rObject.append(courseID)
                    rObject.append(emailsList)
                    eRequestObject.append(rObject)
        except Exception,e:
	    print "exception unenrollment"
            print e
        finally:
            members_csv.close()

        return eRequestObject

def generate_student_grades(request, course_id):
    """ PROD"""
    for_logging = "=====================LOGS START==================<br>"
    import subprocess
    from django.http import HttpResponse
    from util.json_request import JsonResponse

    cur = connection.cursor()
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course_res = CourseOverview.objects.filter(
                                id=course_key,
                            ).order_by('id')

    course = get_course_with_access(request.user, 'staff', course_key, depth=None)
    course_id = str(course_key)
    splitted_course_id = course_id.split('+')
    course_run = splitted_course_id[2]
    for_logging += "<br>===COMPLETECOURSEID===<br>" + course_id +"<br>"
    for_logging += "<br>==SPLITID==<br>" + course_run +"<br>"
    dual_crn = course_run.split('_')
    for_logging += "<br>dual_crn<br>"+", ".join(dual_crn)+"<br>"
    return_str = ""
    for course_id in dual_crn:
	for_logging += "<br>course_id_loop<br>" + course_id+"<br>"
        file_path = "/edx/var/edxapp/media/grades/"+course_id+'.csv'
	for_logging += "<br>==file_path==<br>" + file_path+"<br>"
	file_name = course_id+'.csv'
        grades_data = []
        not_matched = []
        member_staff =[]

        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1
        ).order_by('username').select_related("profile")
        enrolled_students_role = CourseAccessRole.objects.filter(
                                        course_id=course_res,
                                ).order_by('user')
    	# possible extension: implement pagination to show to large courses

        student_info = [
            {
                'username': student.username,
                'id': student.id,
                'email': student.email,
                #'grade_summary': student_grades(student, request, course),
                'grade_summary': CourseGradeFactory().read(student, course).summary,
                'realname': student.profile.name,
            }
            for student in enrolled_students
        ]
        users_instructors = []
        for user in enrolled_students_role:
            users_instructors.append(user.user_id)

        for student in student_info:
            email = student.get('email', None)
            if int(student.get("id")) in users_instructors:
                    member_staff.append(email)
            elif student:
                grade_summary = student.get('grade_summary', False)
                if grade_summary:
                    grade = (grade_summary.get('percent' , None))*100
        
                if email:
			for_logging += "<br>"+email+"<br>"
                        query = ("select sgu_anumber,sgu_username from sgu_users WHERE sgu_email = '{0}' ").format(email)
                        cur.execute(query)
                        user_detail = cur.fetchall()
                        user_detail = [list(elem) for elem in user_detail]
                        user_anumber = [unicode(a[0]) for a in user_detail]
                        user_name = [unicode(a[1]) for a in user_detail]
                    	if not user_detail:
                            user_detail = None
                            not_matched.append(email)
        
                letter_grade = None
                if grade >= 89.5 and grade <= 100:
                    letter_grade = 'A'
                elif grade >= 79.5 and grade <= 89.49:
                    letter_grade = 'B'
                elif grade >= 69.5 and grade <= 79.49:
                    letter_grade = 'C'
                elif grade >= 0 and grade <= 69.49:
                    letter_grade = 'F'

                if user_detail:
                    row = []
                    row.append(course_id)
                    row.append(user_name[0])
                    row.append(user_anumber[0])
                    row.append(grade)
                    row.append(letter_grade)
		    query = ("select * from sgu_members where username='{0}' AND course_id='{1}'").format(user_name[0], course_id)
                    cur.execute(query)
                    users_in_sgu_members = cur.fetchall()
		    if users_in_sgu_members:
                        grades_data.append(row)
		        for_logging += "<br>grades_data"+",".join(str(v) for v in grades_data)+"<br>"

        w = open(file_path, 'w')
        writer = csv.writer(w)
        writer.writerows(grades_data)
        w.close()
        try:
            subprocess.call('/home/ubuntu/SGU_Banner/generate_grades.sh %s' % str(file_name), shell=True)
        except Exception,e:
            raise e
        return_str += '<br>Status:<br>'+file_name+' was successfully sent to sftp area.<br><br>Exceptions:<br>'
        for email in not_matched:
            return_str += '<span style="color:#0048FF">' +email + '</span> was not sent because there is no corresponding user in sgu_users <br>'
        if len(member_staff) > 0:
            for email in member_staff:
                return_str += '<span style="color:#0048FF">' +email + '</span> was excluded because they are staff/instructor on this course <br>'
        for_logging += "<br>LOG END<br>"+"<br>"
 
    return JsonResponse(return_str)
    #return JsonResponse(for_logging+return_str)
def generate_sgux_id(course_id_csv):
     query = ("select id from course_overviews_courseoverview WHERE id LIKE '%{0}%'").format(course_id_csv)
     cur.execute(query)
     c_id = cur.fetchall()
     c_id = c_id[0][0]
     print c_id
     splitted_course_id = c_id.split('+')
     course_run = splitted_course_id[2]
     sgux_id = course_run
     print sgux_id
     return sgux_id

def update_sgux_id():
    query = ("select course_id from sgu_members")
    cur.execute(query)
    ids = cur.fetchall()
    for id in ids:
	id = id[0]
	sgux_id = generate_sgux_id(id)
        query = ("UPDATE sgu_members SET `sgux-id`='{0}' WHERE course_id='{1}'").format(sgux_id,id)
        cur.execute(query)

