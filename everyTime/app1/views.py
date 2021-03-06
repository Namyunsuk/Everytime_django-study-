from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages, auth
from pandas.tests.io.excel.test_openpyxl import openpyxl
from selenium import webdriver
from argon2 import PasswordHasher
from django.views.decorators.csrf import csrf_exempt
from time import sleep
import pandas as pd
from .models import member, friend

@csrf_exempt
def index(request):
    return render(request,"index.html")
@csrf_exempt
def login(request):
    if request.method=="POST":
        ssgid=request.POST.get("userid")
        ssgpw=request.POST.get("userpw")

        if not (ssgid and ssgpw):
            messages.warning(request, "로그인에 실패했습니다!")
            return render(request, 'login.html')
        else:
            #해당 userid,userpw와 일치하는 user객체를 가져온다.
            user=auth.authenticate(request,username=ssgid,password=ssgpw)

            # 해당 user 객체가 존재한다면
            if user is not None:
                auth.login(request,user)
                #에타 정보가 저장되어 있는 member DB
                try:
                    user = member.objects.get(ssgId=ssgid)
                    ssgPw = PasswordHasher().verify(user.ssgPw, ssgpw)
                    request.session['name']=user.name
                    request.session['ETAID'] = user.etaId   #에타 아이디 세션 생성
                    request.session["ETAPW"]=user.etaPw     #에타 비번 세션 생성
                    request.session['FGID']=user.ssgId      #FG 아이디 세션 생성
                    return redirect('button')
                except:
                    messages.warning(request, "로그인에 실패했습니다!")
                    return render(request, 'login.html')
            #존재하지 않는다면
            else:
                # login.html화면으로 돌아감
                messages.warning(request, "로그인에 실패했습니다!")
                return render(request,'login.html')
    # 처음 이 페이지로 왔을 때
    else:
        return render(request,'login.html')

@csrf_exempt
def info(request):
    context={
        'ETAID':request.session['ETAID'],
        'ETAPW':request.session["ETAPW"],
    }
    return context
#----------------로그인 한 후 1번방법으로 친구 목록 가져올지 2번방법으로 친구목록 가져올지 선택하는 창------------------------
@csrf_exempt
def button(request):
    try:
        check=request.session['name']
        if check is not None:
            return render(request,"button.html",{'name':check})
    except:
        return redirect("/login")
#-------------------------------------------------------
@csrf_exempt
def select(request):
    if request.user.is_authenticated:
        name = request.session['name'] #12/29 주석 처리.
        friends=friend.objects.filter(my_name=name) #12/29 주석 처리.

        #if request.method=="POST":
            #return redirect('crawl')

        if name: #12/29 주석 처리.
            #Id.ssgId 하면 member DB의 ssgId(FG 아이디) 가 나오고, Id.ssgPw하면 DB의 FG비번이 나온다.
            #그냥 ID만 쓰면 제일 첫번째 값인 etaId가 나온다.
            return render(request, 'select.html', {'name': name, 'friends': friends, }) #12/29 주석 처리.

    else:
        return redirect('login')
@csrf_exempt
def signup(request):

    # 입력한 아이디, 비번으로 진짜 에타에 접속이 되는지 확인 -하연
    if 'check' in request.POST:
        # 개발용-코드
        user_id = request.POST.get('etaid')  # 개인 아이디 입력
        user_pw = request.POST.get('etapw')  # 비밀번호 입력

        # 이미 가입된 아이디인지 확인-하연
        try:
            member.objects.get(etaId=user_id)
            messages.error(request, '이미 가입된 아이디입니다!')
            return redirect("login")

        except:
            # 로그인 url
            url = 'https://everytime.kr/login'
            options = webdriver.ChromeOptions()
            #options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            # 크롤러 실행 시 로그노출 안되도록 option 설정
            options.add_experimental_option('excludeSwitches', ['enable-logging'])

            driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)

            driver.get(url)

            # id값으로 ID,Password 입력창을 찾아준 후 값 입력
            driver.find_element_by_xpath('//*[@id="container"]/form/p[1]/input').send_keys(user_id)

            sleep(1)

            driver.find_element_by_xpath('//*[@id="container"]/form/p[2]/input').send_keys(user_pw)

            sleep(2)

            # 로그인 버튼 클릭
            driver.find_element_by_xpath('//*[@id="container"]/form/p[3]/input').click()

            # 로그인 성공여부 확인 및 예외처리
            try:
                driver.find_element_by_xpath('//*[@id="menu"]/li[2]/a').click()
                messages.error(request,'에브리타임 아이디와 비밀번호가 확인되었습니다!')
                return render(request,'signup.html',{'etaid': user_id,'etapw':user_pw})

            except:
                driver.quit()
                return 'err'
                messages.error(request, '유효한 에브리타임 정보가 아닙니다!')
                return render(request, "check.html")
            driver.quit()

    # 에타 인증 후 FG 사이트 아이디, 비번 설정
    elif 'signup' in request.POST:
        etaid=request.POST.get("etaid",False)
        etapw=request.POST.get("etapw",False)
        name=request.POST.get("name",False)
        ssgid = request.POST.get("ssgid",False)
        ssgpw = request.POST.get("ssgpw",False)
        ressgpw = request.POST.get("ressgpw",False)

        if (ssgpw == ressgpw):
            messages.error(request, '정상적으로 회원가입이 되었습니다!')

            #내가 만든 DB(에타정보, FD정보 둘다 저장)
            DB=member(name=name,etaId=etaid,etaPw=etapw,ssgId=ssgid,ssgPw=PasswordHasher().hash(ssgpw))
            DB.save()
            #장고에서 제공하는 로그인 기능DB활용
            user=User.objects.create_user(username=ssgid,password=ssgpw)
            auth.login(request,user)
            return redirect('/button')

        else:
            messages.error(request, '비밀번호가 다릅니다!')
            return render(request, "check.html")

    else:  # 맨 처음에 이 페이지로 들어올 때 -하연
        return render(request,"check.html")
    return render(request, "check.html")

@csrf_exempt
def findpw(request):
    if request.method=="POST":
        name=request.POST.get('name',False)
        etaid=request.POST.get('etaid',False)
        etapw=request.POST.get('etapw',False)
        ssgpw=request.POST.get('ssgpw',False)
        ressgpw=request.POST.get('ressgpw',False)

        if ssgpw==ressgpw:
            try:
                print(1)
                member_db=member.objects.get(name=name,etaId=etaid,etaPw=etapw)
                print(2)
                member_db.ssgPw=PasswordHasher().hash(ssgpw)
                print(3)
                member_db.save()
                print(4)
                user_db=User.objects.get(username=member_db.ssgId)
                print(5)
                user_db.set_password(ssgpw)
                print(6)
                user_db.save()
                print(7)
                return redirect("/login")
            except:
                messages.warning(request, "정확한 정보를 입력해주세요123.")
                return render(request,"findpw.html")
        else:
            messages.warning(request,"정확한 정보를 입력해주세요.234")
            return render(request, "findpw.html")

    return render(request,"findpw.html")
@csrf_exempt
def timetable_upload(request):
    if request.user.is_authenticated is False:
        return redirect("login")
    if 'upload' in request.POST:
        def class_array(class_day, class_time):
            if class_day == '월':
                mon.append(class_time)
            if class_day == '화':
                tue.append(class_time)
            if class_day == '수':
                wed.append(class_time)
            if class_day == '목':
                thur.append(class_time)
            if class_day == '금':
                fri.append(class_time)

        excel = request.FILES['excel']

        if excel.name[-4:] != 'xlsx':
            print('err')
            return redirect('/login/')

        wb = openpyxl.load_workbook(excel)
        ws = wb.active
        # 불필요한 행 삭제
        ws.delete_rows(1, 3)
        ws.delete_cols(1, 11)

        ws.delete_cols(2)
        df = pd.DataFrame(ws.values)

        # 엑셀 값에서 value값만 저장
        class_list = list(df[0])

        # 강의 시간이 없는 부분 삭제
        class_list = list(filter(None, class_list))

        mon = []
        tue = []
        wed = []
        thur = []
        fri = []

        for i in class_list:
            tmp = i.index('(')
            class_ = i[0:tmp]
            class_time = class_[-11:]
            class_day = class_[0:-11]
            start_time = int(class_time[0:2]) * 100 + int(class_time[3:5])
            end_time = int(class_time[6:8]) * 100 + int(class_time[9:11])
            f_class_time = str(start_time) + '-' + str(end_time)
            for i in class_day:
                class_array(i, f_class_time)


        #DB에 이름 , 시간 저장-하연
        name=request.session['name']
        user_name = request.POST["name"]
        #print(name)
        #print(user_name)
        #DB=excel_db(my_name=name,friend_name=user_name,mon=mon,tue=tue,wed=wed,thu=thur,fri=fri)
        try:
            existDB=friend.objects.get(my_name=name)
            messages.warning(request,"이미 등록된 이름입니다!")
            return render(request,"excel.html")
            
        except:
            DB=friend(my_name=name,friend_name=user_name,mon=mon,tue=tue,wed=wed,thu=thur,fri=fri)
            DB.save()
            messages.warning(request, "성공적으로 업로드 하였습니다!")
            return redirect("excel")

    elif 'submit' in request.POST:
        return redirect("/gongang")
    # 값만 저장. 페이지 이동이 아니라.
    # DB에 잘 들어갔는지 확인하기

    else:
        return render(request, "excel.html")
@csrf_exempt
def gongang(request):
    if request.method=='POST':
        selected=request.POST.getlist('selected')
        if selected is True:
        #DB에 저장된 친구 이름중에 있는지 확인하기
        #for i in selected:
            #selectDB=friend.objects.filter(friend_name=i)
            #for j in selectDB:
                #print(j.friend_name)
                #print(j.mon)
                #print(j.tue)
                #print(j.wed)
                #print(j.thu)
                #print(j.fri)
            return render(request,"gongang.html")
    return redirect('button')

def logout(request):
    print(request.session['name'])
    auth.logout(request)
    return redirect('/')