from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import re
from django.contrib.auth.hashers import check_password, make_password
from datetime import date, datetime, timedelta
from django.db.models import Max
from django.utils.timezone import localtime

def getUser(request):
    userID = request.session.get('userID')
    subAdminID = request.session.get('subAdminID')
    superAdminID = request.session.get('superAdminID')

    user = None
    base = None
    subAdmin = None
    superAdmin = None

    # Check if it's a user or subAdmin session
    if userID:
        user = UpdatedUser.objects.get(userID=userID)
        base = 'base/userBase.html'
    elif subAdminID:
        subAdmin = SignUP.objects.get(subAdminID=subAdminID)
        user = UpdatedUser.objects.get(userPhone=subAdmin.subAdminPhone)
        base = 'base/subAdminBase.html'
    elif superAdminID:
        superAdmin = SuperAdmin.objects.get(superAdminID=superAdminID)
        base = 'base/superAdminBase.html'
    else:
        return redirect('adminSignIn')

    return {'user': user, 'base': base, 'subAdmin': subAdmin, 'superAdmin': superAdmin}


# All List Function are here
def listDSC(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    whatsapp_url = request.session.pop('whatsapp_url', None)

    updatedDSCs = UpdatedDSC.objects.filter(subAdminID=user.subAdminID).all().order_by('-modifiedDate')
    
    today = date.today()
    for dsc in updatedDSCs:
        dsc.is_expired = dsc.renewalDate.date() < today

    context = {
        'base': base,
        'updatedDSCs': updatedDSCs,
        'user': user,
        'whatsurl': whatsapp_url 
    }
    return render(request, 'dsc/listDSC.html', context)

def listCompany(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
            
    companies = UpdatedCompany.objects.filter(subAdminID=user.subAdminID).all().order_by('-companyModifiedDate')
    context = {
        'base': base,
        'companies': companies,
        'user': user
    }
    return render(request, 'company/listCompany.html', context)

def listGroup(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
            
    groups = UpdatedGroup.objects.filter(subAdminID=user.subAdminID).all().order_by('-groupModifiedDate')
    context = {
        'base': base,
        'groups':groups,
        'user': user
    }
    return render(request, 'group/listGroup.html', context)

def listClient(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
            
    clients = UpdatedClient.objects.filter(subAdminID=user.subAdminID).all().order_by('-clientModifiedDate')
    context = {
        'base': base,
        'clients': clients,
        'user': user
    }
    return render(request, 'client/listClient.html', context)

def listWork(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    work = Work.objects.filter(subAdminID=user.subAdminID).all()
    context = {
        'base': base,
        'user': user,
        'work': work
    }
    return render(request, 'work/listWork.html', context)

def listPendingWork(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    # Determine if the user wants to see archived records.
    show_archived = request.GET.get('archived', 'false').lower() == 'true'

    if show_archived:
        pendingWork = PendingWork.objects.filter(subAdminID=user.subAdminID, isArchived=True)
    else:
        pendingWork = PendingWork.objects.filter(subAdminID=user.subAdminID, isArchived=False)

    # Order so that pinned rows appear first.
    pendingWork = pendingWork.order_by('-isPinned', '-srnDate')  # Adjust ordering as needed.

    today = localtime().date()  # Get today's system date

    # Apply conditions for due date and status
    for work in pendingWork:
        # Internal Due Date Conditions
        if work.internalDueDate:  # Assuming this field exists
            internal_due_date = work.internalDueDate
            actual_due_date = work.actualDueDate
            days_remaining = (actual_due_date - internal_due_date).days

            work.is_expired = days_remaining < 0  # Red color condition
            work.is_due_soon = 0 <= days_remaining < 4  # Orange color condition

        # Status Formatting Flags
        work.is_approved = work.status == "Approved"
        work.is_marked_for_resubmission = work.status == "Sent For Resubmission"
        work.is_pending_for_approval = work.status == "Pending For Approval"
        work.is_rejected = work.status == "Rejected"

    context = {
        'base': base,
        'user': user,
        'pendingWork': pendingWork,
        'show_archived': show_archived
    }
    return render(request, 'pendingWork/listPendingWork.html', context)

def listAnnual(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
    
    # Determine if the user wants to see archived records.
    show_archived = request.GET.get('archived', 'false').lower() == 'true'
    
    if show_archived:
        annualFilies = AnnualFiling.objects.filter(subAdminID=user.subAdminID, isArchived=True)
    else:
        annualFilies = AnnualFiling.objects.filter(subAdminID=user.subAdminID, isArchived=False)
    
    # Order so that pinned rows appear at the top.
    annualFilies = annualFilies.order_by('-isPinned', '-financialYear')
    
    context = {
        'base': base,
        'user': user,
        'annualFilies': annualFilies,
        'show_archived': show_archived,
    }
    return render(request, 'annualFiling/listAnnual.html', context)

def listReport(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
    pendingWork = PendingWork.objects.filter(subAdminID=user.subAdminID).all()
    context = {
        'base': base,
        'user': user,
        'pendingWork': pendingWork,
    }
    return render(request, 'report/listReport.html', context)


# All Add Function are here
def addDSC(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    # Fetch the user's subscription plan
    subscription_plan = SubAdminSubscription.objects.filter(subAdminID=user.subAdminID, isActive='True').first()
    subscription_plan_name = subscription_plan.planID.planName.lower()
    if subscription_plan_name == 'free trial':
        max_dsc_allowed = 100
    elif subscription_plan_name == 'basic':
        max_dsc_allowed = 350
    elif subscription_plan_name == 'standard':
        max_dsc_allowed = 700
    elif subscription_plan_name == 'premimum':
        max_dsc_allowed = 1500
    else:
        max_dsc_allowed = float('inf')

    # Count existing DSCs for the user
    existing_dsc_count = UpdatedDSC.objects.filter(subAdminID=user.subAdminID).count()

    companies = UpdatedCompany.objects.filter(subAdminID=user.subAdminID).all()
    context = {
        'base': base,
        'companies': companies,
        'user': user
    }

    if request.method == 'POST':
        clientName = request.POST.get('clientName')
        companyName = request.POST.get('companyName')
        status = request.POST.get('status')
        location = request.POST.get('location')
        renewalDate = request.POST.get('renewalDate', '')
        receivedBy = request.POST.get('receivedBy', '')
        receivedFrom = request.POST.get('receivedFrom', '')
        clientPhone = request.POST.get('clientPhone')
        deliveredTo = request.POST.get('deliveredTo', '')
        deliveredBy = request.POST.get('deliveredBy', '')

        # Check if renewalDate is provided, otherwise set it to None
        renewalDate = renewalDate if renewalDate else None

        # Prepare the form data to retain values on error
        form_data = {
            'clientName': clientName,
            'companyName': companyName,
            'status': status,
            'location': location,
            'renewalDate': renewalDate,
            'receivedBy': receivedBy,
            'receivedFrom': receivedFrom,
            'clientPhone': clientPhone,
            'deliveredTo': deliveredTo,
            'deliveredBy': deliveredBy
        }

        # Validation checks
        if not all([clientName, companyName, status, location]):
            messages.error(request, "Please fill all required fields.")
        elif existing_dsc_count >= max_dsc_allowed:
            messages.error(request, f"You can only add up to {max_dsc_allowed} DSCs based on your subscription plan.")
        else:
            subAdminID = user.subAdminID
            company = UpdatedCompany.objects.filter(companyName=companyName, subAdminID=subAdminID).first()

            if company:
                dsc = UpdatedDSC(
                    clientName=clientName,
                    companyID=company,
                    status=status,
                    receivedBy=receivedBy,
                    receivedFrom=receivedFrom,
                    deliveredTo=deliveredTo,
                    deliveredBy=deliveredBy,
                    location=location,
                    renewalDate=renewalDate,
                    clientPhone=clientPhone,
                    userID=user,
                    subAdminID=subAdminID
                )
                dsc.save()

                dscHistory = HistoryDSC(
                    dscID=dsc,
                    clientName=clientName,
                    companyID=company,
                    status=status,
                    receivedBy=receivedBy,
                    receivedFrom=receivedFrom,
                    deliveredTo=deliveredTo,
                    deliveredBy=deliveredBy,
                    location=location,
                    renewalDate=renewalDate,
                    clientPhone=clientPhone,
                    userID=user,
                    subAdminID=subAdminID,
                    modifiedDate=dsc.modifiedDate
                )
                dscHistory.save()

                # Conditional field updates based on status
                if status == 'IN':
                    whatsapp_url = send_whatsapp_message(phone_number=clientPhone, client_name=clientName, status=status, person=dsc.receivedFrom)
                elif status == 'OUT':
                    whatsapp_url = send_whatsapp_message(phone_number=clientPhone, client_name=clientName, status=status, person=dsc.deliveredTo)

                request.session['whatsapp_url'] = whatsapp_url
                messages.success(request, "DSC added successfully.")

                return HttpResponseRedirect(reverse('listDSC'))
            else:
                messages.error(request, "Company not found.")
                form_data['companyName'] = ''  # Clear the companyName field in case of error

        # Return the form with the existing values except for the cleared fields
        context['form_data'] = form_data
        return render(request, 'dsc/addDSC.html', context)

    return render(request, 'dsc/addDSC.html', context)

def addCompany(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    groups = UpdatedGroup.objects.filter(subAdminID=user.subAdminID).all()
    context = {
        'base': base,
        'groups': groups,
        'user': user
    }

    if request.method == 'POST':
        groupName = request.POST.get('groupName')
        companyName = request.POST.get('companyName')
        companyType = request.POST.get('companyType')

        # Prepare form data to retain values in case of error
        form_data = {
            'groupName': groupName,
            'companyName': companyName,
            'companyType': companyType
        }

        # Validation checks
        if not groupName or not companyName or not companyType:
            messages.error(request, "Please fill all required fields.")
        else:
            subAdminID = user.subAdminID
            group = UpdatedGroup.objects.filter(groupName=groupName, subAdminID=subAdminID).first()

            if group:
                # Normalize the company name for case-insensitive comparison
                companyName_normalized = companyName.lower()

                if UpdatedCompany.objects.filter(companyName__iexact=companyName_normalized, subAdminID=subAdminID).exists():
                    messages.error(request, "Company already exists.")
                    form_data['companyName'] = ''  # Clear the company name in case of this error
                else:
                    company = UpdatedCompany(
                        companyName=companyName,companyType=companyType, groupID=group, userID=user, subAdminID=subAdminID
                    )
                    company.save()

                    companyHistory = HistoryCompany(
                        companyID=company, companyName=companyName,companyType=companyType, groupID=group,
                        userID=user, subAdminID=subAdminID, companyModifiedDate=company.companyModifiedDate
                    )
                    companyHistory.save()

                    messages.success(request, "Company added successfully.")
                    return HttpResponseRedirect(reverse('listCompany'))
            else:
                messages.error(request, "Group not found.")
                form_data['groupName'] = ''  # Clear the group name if the group is not found

        # If there's any error, re-render the form with previous data
        context['form_data'] = form_data
        return render(request, 'company/addCompany.html', context)

    return render(request, 'company/addCompany.html', context)

def addGroup(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
            
    context = {
        'base': base,
        'user': user
    }
    if request.method == 'POST':
        groupName = request.POST.get('groupName')

        if not groupName:
            messages.error(request, "Group name cannot be empty.")
            return redirect(request.path)
        else:
            if user:
                subAdminID = user.subAdminID
                # Normalize the group name to make it case-insensitive
                groupName_normalized = groupName.lower()
                if UpdatedGroup.objects.filter(groupName__iexact=groupName_normalized, subAdminID=subAdminID).exists():
                    messages.error(request, "Group already exists.")
                    return redirect(request.path)
                else:
                    group = UpdatedGroup(
                        groupName=groupName, userID=user, subAdminID=subAdminID
                    )
                    group.save()

                    groupHistory = HistoryGroup(
                        groupID=group, groupName=groupName, userID=user,
                        subAdminID=subAdminID, groupModifiedDate=group.groupModifiedDate
                    )
                    groupHistory.save()
                    messages.success(request, "Group added successfully.")
                    return HttpResponseRedirect(reverse('listGroup'))

    
    return render(request, 'group/addGroup.html', context)

def addClient(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    # Fetch companies that do not have a client associated with them
    companies_with_no_clients = UpdatedCompany.objects.filter(
        subAdminID=user.subAdminID
    ).exclude(
        updatedclient__isnull=False
    )
    context = {
        'base': base,
        'companies': companies_with_no_clients
    }

    if request.method == 'POST':
        clientName = request.POST.get('clientName')
        companyName = request.POST.get('companyName')
        clientPhone = request.POST.get('clientPhone')

        # Prepare form data to retain values in case of error
        form_data = {
            'clientName': clientName,
            'companyName': companyName,
            'clientPhone': clientPhone
        }

        # Check if all fields are filled
        if not all([clientName, companyName, clientPhone]):
            messages.error(request, "Please fill all required fields.")
        elif not re.match(r'^[A-Za-z\s]+$', clientName):
            messages.error(request, "Client name can only contain letters and spaces.")
            form_data['clientName'] = ''  # Clear client name field in case of error
        elif not re.match(r'^\d{10}$', clientPhone):
            messages.error(request, "Phone number must be exactly 10 digits.")
            form_data['clientPhone'] = ''  # Clear phone number in case of error
        else:
            # Check if the phone number already exists
            subAdminID = user.subAdminID
            company = UpdatedCompany.objects.filter(companyName=companyName, subAdminID=subAdminID).first()

            if company:
                if UpdatedClient.objects.filter(clientPhone=clientPhone).exists():
                    messages.error(request, "Phone number already exists.")
                    form_data['clientPhone'] = ''  # Clear phone field
                else:
                    # Create and save the new client
                    client = UpdatedClient(
                        clientName=clientName, companyID=company, userID=user,
                        clientPhone=clientPhone, subAdminID=subAdminID
                    )
                    client.save()

                    # Save the client to the history
                    clientHistory = HistoryClient(
                        clientID=client, clientName=clientName, companyID=company,
                        userID=user, clientPhone=clientPhone,
                        subAdminID=subAdminID, clientModifiedDate=client.clientModifiedDate
                    )
                    clientHistory.save()

                    messages.success(request, "Client added successfully.")
                    return HttpResponseRedirect(reverse('listClient'))
            else:
                messages.error(request, "Company not found.")
                form_data['companyName'] = ''  # Clear company name if not found

        # If there are any errors, re-render the form with previous data
        context['form_data'] = form_data
        return render(request, 'client/addClient.html', context)

    return render(request, 'client/addClient.html', context)

def addWork(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
    context = {
        'base': base,
    }
    
    if request.method == 'POST':
        formNo = request.POST.get('formNo')
        matter = request.POST.get('matter')
        filingDays = request.POST.get('filingDays')
        
        # Prepare form data to retain values in case of errors
        form_data = {
            'formNo': formNo,
            'matter': matter,
            'filingDays': filingDays,
        }
        
        # Validate that all required fields are provided
        if not all([formNo, matter, filingDays]):
            messages.error(request, "Please fill all required fields.")
        # Check that filingDays is numeric
        elif not filingDays.isdigit():
            messages.error(request, "Filing days must be a number.")
            form_data['filingDays'] = ''
        # Check if formNo already exists for this sub-admin
        elif Work.objects.filter(formNo=formNo, subAdminID=user.subAdminID).exists():
            messages.error(request, "Form number already exists.")
        else:
            try:
                # Create and save a new Work record
                work = Work(
                    subAdminID=user.subAdminID,  # Assumes 'user' is an instance of SignUp
                    formNo=formNo,
                    matter=matter,
                    filingDays=int(filingDays),
                    modifiedBy=user,
                )
                work.save()
                historyWork = HistoryWork(
                    formID=work,
                    subAdminID=user.subAdminID,  # Assumes 'user' is an instance of SignUp
                    formNo=formNo,
                    matter=matter,
                    filingDays=int(filingDays),
                    modifiedBy=user,
                    modifiedDate=work.modifiedDate
                )
                historyWork.save()
                messages.success(request, "Work added successfully.")
                return HttpResponseRedirect(reverse('listWork'))
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        
        # If there are errors, pass the form data back to the template
        context['form_data'] = form_data
        return render(request, 'work/addWork.html', context)
    
    return render(request, 'work/addWork.html', context)

def addPendingWork(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
    companies = UpdatedCompany.objects.filter(subAdminID=user.subAdminID).all()
    forms = Work.objects.filter(subAdminID=user.subAdminID).all()
    users = UpdatedUser.objects.filter(subAdminID=user.subAdminID, isActive="True").all()
    context = {
        'base': base,
        'companies': companies,
        'forms': forms,
        'users': users,
        'user': user
    }

    if request.method == 'POST':
        # Get data from POST request
        form_no           = request.POST.get('formNo')            # form number from the input
        company_name      = request.POST.get('companyName')         # company name from the input
        event_date        = request.POST.get('eventDate')
        actual_due_date   = request.POST.get('actualDueDate')
        cutOffTime        = request.POST.get('cutOffTime')          # used for internal due date calculation
        srnNo             = request.POST.get('srnNo', '')
        internal_due_date = request.POST.get('internalDueDate')
        user_id_str       = request.POST.get('userID')
        status            = request.POST.get('status')
        srn_date_str      = request.POST.get('srnDate', '')
        amt_str           = request.POST.get('amt', '')
        remark            = request.POST.get('remark')
        billing           = request.POST.get('billing')
        fees              = request.POST.get('fees', '')
        
        # For checkboxes, use membership test (if checked, the field appears in POST)
        isArchived = 'isArchived' in request.POST
        isPinned   = 'isPinned' in request.POST

        company = UpdatedCompany.objects.filter(companyName=company_name, subAdminID=user.subAdminID).first()
        groupName = company.groupID.groupName
        # Prepare form data to repopulate form in case of error

        form_data = request.POST.copy()
        form_data['groupName'] = groupName
        

        # Check required fields (optional fields for srnNo, srnDate, and amt are not required)
        if not all([form_no, company_name, event_date, actual_due_date, 
                    cutOffTime, user_id_str, status, billing]):
            messages.error(request, "Please fill all required fields.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)
        
        # Helper functions to parse optional fields
        def parse_date(date_str):
            if date_str:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        def parse_amount(amt_str):
            try:
                return float(amt_str) if amt_str else None 
            except ValueError:
                return None

        srnDate = parse_date(srn_date_str)
        amt = parse_amount(amt_str)
        fees = parse_amount(fees)
        
        # Fetch foreign key objects:
        try:
            work_instance = Work.objects.get(formNo=form_no, subAdminID=user.subAdminID)
        except Work.DoesNotExist:
            messages.error(request, "Work record not found.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)
        
        try:
            company_instance = UpdatedCompany.objects.get(companyName=company_name, subAdminID=user.subAdminID)
        except UpdatedCompany.DoesNotExist:
            messages.error(request, "Company record not found.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)
        
        try:
            updated_user_instance = UpdatedUser.objects.filter(userName=user_id_str, subAdminID=user.subAdminID).first()
        except UpdatedUser.DoesNotExist:
            messages.error(request, "User record not found.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)
        
        # --- Auto-generate indexSRN for the current subAdminID ---
        max_index_dict = PendingWork.objects.filter(subAdminID=user.subAdminID).aggregate(max_index=Max('indexSRN'))
        max_index = max_index_dict.get('max_index')
        try:
            next_index = int(max_index) + 1 if max_index is not None else 1
        except Exception:
            next_index = 1
        # ----------------------------------------------------------
        
        # Create and save the PendingWork record (with indexSRN included)
        try:
            pending_work = PendingWork(
                subAdminID=user.subAdminID,
                formID=work_instance,
                companyID=company_instance,
                eventDate=event_date,
                cutOffTime=cutOffTime,
                internalDueDate=internal_due_date,
                actualDueDate=actual_due_date,
                userID=updated_user_instance,
                status=status,
                srnNo=srnNo,      # remains as provided (or empty)
                srnDate=srnDate,
                amt=amt,
                remark=remark,
                billing=billing,
                fees=fees,
                isArchived=isArchived,
                isPinned=isPinned,
                indexSRN=next_index,  # New auto-increment field for the subAdmin
            )
            pending_work.save()
            
            # Optionally, create a history record as well
            history_pending_work = HistoryPendingWork(
                pendingWorkID=pending_work,
                subAdminID=user.subAdminID,
                formID=work_instance,
                companyID=company_instance,
                eventDate=event_date,
                cutOffTime=cutOffTime,
                internalDueDate=internal_due_date,
                actualDueDate=actual_due_date,
                userID=updated_user_instance,
                status=status,
                srnNo=srnNo,
                srnDate=srnDate,
                amt=amt,
                remark=remark,
                billing=billing,
                fees=fees,
                isArchived=isArchived,
                isPinned=isPinned,
                indexSRN=next_index,
                modifiedDate=pending_work.modifiedDate  # assuming this field exists
            )
            history_pending_work.save()
            
            messages.success(request, "Pending work added successfully.")
            return HttpResponseRedirect(reverse('listPendingWork'))
        except Exception as e:
            messages.error(request, f"Error saving pending work: {e}")
            context['form_data'] = form_data
            return render(request, 'pendingWork/addPendingWork.html', context)
    
    return render(request, 'pendingWork/addPendingWork.html', context)

def addAnnual(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
    companies = UpdatedCompany.objects.filter(subAdminID=user.subAdminID).all()
    context = {
        'base': base,
        'user': user,
        'companies': companies
    }

    if request.method == 'POST':
        # Retrieve data from POST request
        company_name       = request.POST.get('companyName')  # from the form
        financialYear      = request.POST.get('financialYear')
        
        statusDPT3         = request.POST.get('statusDPT3', 'N/A')
        srnNoDPT3          = request.POST.get('srnNoDPT3')
        srnDateDPT3_str    = request.POST.get('srnDateDPT3')
        amtDPT3_str        = request.POST.get('amtDPT3')
        
        statusMGT14        = request.POST.get('statusMGT14', 'N/A')
        srnNoMGT14         = request.POST.get('srnNoMGT14')
        srnDateMGT14_str   = request.POST.get('srnDateMGT14')
        amtMGT14_str       = request.POST.get('amtMGT14')
        
        statusAOC4         = request.POST.get('statusAOC4', 'N/A')
        srnNoAOC4          = request.POST.get('srnNoAOC4')
        srnDateAOC4_str    = request.POST.get('srnDateAOC4')
        amtAOC4_str        = request.POST.get('amtAOC4')
        
        statusMGT7         = request.POST.get('statusMGT7', 'N/A')
        srnNoMGT7          = request.POST.get('srnNoMGT7')
        srnDateMGT7_str    = request.POST.get('srnDateMGT7')
        amtMGT7_str        = request.POST.get('amtMGT7')
        
        statusForm11       = request.POST.get('statusForm11', 'N/A')
        srnNoForm11        = request.POST.get('srnNoForm11')
        srnDateForm11_str  = request.POST.get('srnDateForm11')
        amtForm11_str      = request.POST.get('amtForm11')
        
        statusForm8        = request.POST.get('statusForm8', 'N/A')
        srnNoForm8         = request.POST.get('srnNoForm8')
        srnDateForm8_str   = request.POST.get('srnDateForm8')
        amtForm8_str       = request.POST.get('amtForm8')
        
        isArchived         = 'isArchived' in request.POST
        isPinned           = 'isPinned' in request.POST


        
        company = UpdatedCompany.objects.filter(companyName=company_name, subAdminID=user.subAdminID).first()
        groupName = company.groupID.groupName
        # Prepare form data to repopulate form in case of error

        form_data = request.POST.copy()
        form_data['groupName'] = groupName

        # Validate required fields
        if not company_name or not financialYear:
            messages.error(request, "Company name and Financial Year are required.")
            context['form_data'] = form_data
            return render(request, 'annualFiling/addAnnual.html', context)

        # Look up the company record using the provided company name and current sub-admin
        try:
            company = UpdatedCompany.objects.get(companyName=company_name, subAdminID=user.subAdminID)
        except UpdatedCompany.DoesNotExist:
            messages.error(request, "Company not found.")
            context['form_data'] = form_data
            return render(request, 'annualFiling/addAnnual.html', context)

        # Helper functions to parse dates and amounts
        def parse_date(date_str):
            if date_str:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        def parse_amount(amt_str):
            try:
                return float(amt_str) if amt_str else 0.0
            except ValueError:
                return 0.0

        srnDateDPT3   = parse_date(srnDateDPT3_str)
        srnDateMGT14  = parse_date(srnDateMGT14_str)
        srnDateAOC4   = parse_date(srnDateAOC4_str)
        srnDateMGT7   = parse_date(srnDateMGT7_str)
        srnDateForm11 = parse_date(srnDateForm11_str)
        srnDateForm8  = parse_date(srnDateForm8_str)

        amtDPT3   = parse_amount(amtDPT3_str)
        amtMGT14  = parse_amount(amtMGT14_str)
        amtAOC4   = parse_amount(amtAOC4_str)
        amtMGT7   = parse_amount(amtMGT7_str)
        amtForm11 = parse_amount(amtForm11_str)
        amtForm8  = parse_amount(amtForm8_str)

        try:
            # Create the AnnualFiling record without indexSRN first.
            af = AnnualFiling.objects.create(
                subAdminID     = user.subAdminID,
                companyID      = company,
                financialYear  = financialYear,
                
                statusDPT3     = statusDPT3,
                srnNoDPT3      = srnNoDPT3,
                srnDateDPT3    = srnDateDPT3,
                amtDPT3        = amtDPT3,
                
                statusMGT14    = statusMGT14,
                srnNoMGT14     = srnNoMGT14,
                srnDateMGT14   = srnDateMGT14,
                amtMGT14       = amtMGT14,
                
                statusAOC4     = statusAOC4,
                srnNoAOC4      = srnNoAOC4,
                srnDateAOC4    = srnDateAOC4,
                amtAOC4        = amtAOC4,
                
                statusMGT7     = statusMGT7,
                srnNoMGT7      = srnNoMGT7,
                srnDateMGT7    = srnDateMGT7,
                amtMGT7        = amtMGT7,
                
                statusForm11   = statusForm11,
                srnNoForm11    = srnNoForm11,
                srnDateForm11  = srnDateForm11,
                amtForm11      = amtForm11,
                
                statusForm8    = statusForm8,
                srnNoForm8     = srnNoForm8,
                srnDateForm8   = srnDateForm8,
                amtForm8       = amtForm8,
                
                isArchived     = isArchived,
                isPinned       = isPinned,
                modifiedBy=user
            )
            # --- Auto-generate indexSRN for AnnualFiling for the current subAdminID ---
            max_index_dict = AnnualFiling.objects.filter(subAdminID=user.subAdminID).aggregate(max_index=Max('indexSRN'))
            max_index = max_index_dict.get('max_index')
            try:
                next_index = int(max_index) + 1 if max_index is not None else 1
            except Exception:
                next_index = 1
            af.indexSRN = next_index
            af.save()
            # Optionally, create a history record for AnnualFiling.
            historyaf = HistoryAnnualFiling(
                annualFilingID = af,
                subAdminID     = user.subAdminID,
                companyID      = company,
                financialYear  = financialYear,
                
                statusDPT3     = statusDPT3,
                srnNoDPT3      = srnNoDPT3,
                srnDateDPT3    = srnDateDPT3,
                amtDPT3        = amtDPT3,
                
                statusMGT14    = statusMGT14,
                srnNoMGT14     = srnNoMGT14,
                srnDateMGT14   = srnDateMGT14,
                amtMGT14       = amtMGT14,
                
                statusAOC4     = statusAOC4,
                srnNoAOC4      = srnNoAOC4,
                srnDateAOC4    = srnDateAOC4,
                amtAOC4        = amtAOC4,
                
                statusMGT7     = statusMGT7,
                srnNoMGT7      = srnNoMGT7,
                srnDateMGT7    = srnDateMGT7,
                amtMGT7        = amtMGT7,
                
                statusForm11   = statusForm11,
                srnNoForm11    = srnNoForm11,
                srnDateForm11  = srnDateForm11,
                amtForm11      = amtForm11,
                
                statusForm8    = statusForm8,
                srnNoForm8     = srnNoForm8,
                srnDateForm8   = srnDateForm8,
                amtForm8       = amtForm8,
                
                isArchived     = isArchived,
                isPinned       = isPinned,
                modifiedDate   = af.modifiedDate,
                indexSRN       = af.indexSRN,
                modifiedBy=user
            )
            historyaf.save()
            messages.success(request, "Annual Filing added successfully!")
            return HttpResponseRedirect(reverse('listAnnual'))
        except Exception as e:
            messages.error(request, f"Error saving Annual Filing: {e}")
            context['form_data'] = form_data
            return render(request, 'annualFiling/addAnnual.html', context)
    return render(request, 'annualFiling/addAnnual.html', context)


# All Update Function are here
def updateDSC(request, dscID):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    companies = UpdatedCompany.objects.filter(subAdminID=user.subAdminID).all()
    dsc = UpdatedDSC.objects.filter(subAdminID=user.subAdminID, dscID=dscID).first()
    dscHistory = HistoryDSC.objects.filter(subAdminID=user.subAdminID, dscID=dscID).all().order_by('-modifiedDate')

    # Try to get the client for receivedFrom and deliveredTo; fallback to dsc's values if not found
    try:
        client = UpdatedClient.objects.get(companyID=dsc.companyID)
        receivedFrom = client.clientName
        deliveredTo = client.clientName
        clientPhone = client.clientPhone
    except UpdatedClient.DoesNotExist:
        client = None
        receivedFrom = dsc.receivedFrom  # Fallback to previous value
        deliveredTo = dsc.deliveredTo    # Fallback to previous value
        clientPhone = dsc.clientPhone

    context = {
        'base': base,
        'dsc': dsc,
        'dscHistory': dscHistory,
        'user': user,
        'companies': companies,
        'options': ['IN', 'OUT'],
        'receivedFrom': receivedFrom,
        'deliveredTo': deliveredTo,
        'clientPhone': clientPhone
    }
    
    if request.method == 'POST':
        clientName = request.POST.get('clientName')
        companyName = request.POST.get('companyName')
        status = request.POST.get('status')
        location = request.POST.get('location')
        renewalDate = request.POST.get('renewalDate')
        receivedBy = request.POST.get('receivedBy', '')
        clientPhone = request.POST.get('clientPhone')
        receivedFrom = request.POST.get('receivedFrom', '')
        deliveredTo = request.POST.get('deliveredTo', '')
        deliveredBy = request.POST.get('deliveredBy', '')

        # Check if renewalDate is provided, otherwise set it to None
        renewalDate = renewalDate if renewalDate else None

        if not all([clientName, companyName, status, location]):
            messages.error(request, "Please fill all required fields.")
            return redirect(request.path)
        else:
            if user:
                company = UpdatedCompany.objects.filter(companyName=companyName, subAdminID=user.subAdminID).first()

                if company:
                    dsc.clientName = clientName
                    dsc.companyID = company
                    dsc.status = status
                    dsc.location = location
                    dsc.renewalDate = renewalDate
                    dsc.userID = user
                    
                    # Conditional field updates based on status
                    if status == 'IN':
                        dsc.receivedFrom = receivedFrom
                        dsc.receivedBy = receivedBy
                        dsc.deliveredTo = ''  # Set to an empty string instead of None when status is IN
                        dsc.deliveredBy = ''
                        whatsapp_url = send_whatsapp_message(phone_number=clientPhone, client_name=clientName, status=status, person=dsc.receivedFrom)
                    elif status == 'OUT':
                        dsc.deliveredTo = deliveredTo
                        dsc.deliveredBy = deliveredBy
                        dsc.receivedFrom = ''  # Set to an empty string instead of None when status is OUT
                        dsc.receivedBy = ''    # Set to an empty string instead of None when status is OUT
                        whatsapp_url = send_whatsapp_message(phone_number=clientPhone, client_name=clientName, status=status, person=dsc.deliveredTo)

                    dsc.clientPhone = clientPhone
                    dsc.save()

                    # Save history
                    dscHistory = HistoryDSC(
                        dscID=dsc, clientName=clientName, companyID=company, status=status, receivedBy=receivedBy, 
                        receivedFrom=receivedFrom, deliveredTo=deliveredTo, deliveredBy=deliveredBy, location=location, renewalDate=renewalDate, 
                        clientPhone=clientPhone, userID=user, subAdminID=user.subAdminID, modifiedDate=dsc.modifiedDate
                    )
                    dscHistory.save()

                    # Re-fetch updated DSC from the database
                    dsc = UpdatedDSC.objects.filter(subAdminID=user.subAdminID, dscID=dscID).first()

                    # Send WhatsApp message
                    messages.success(request, "DSC updated successfully.")
                    
                    # Update context with the re-fetched DSC and WhatsApp URL
                    context['dsc'] = dsc
                    context['whatsurl'] = whatsapp_url

                    return render(request, 'dsc/updateDSC.html', context)
                else:
                    messages.error(request, "Company not found.")
                    return redirect(request.path)
          
    return render(request, 'dsc/updateDSC.html', context)

def updateCompany(request, companyID):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
            
    company = UpdatedCompany.objects.get(companyID=companyID)
    companyHistory = HistoryCompany.objects.filter(companyID=companyID).all().order_by('-companyModifiedDate')
    groups = UpdatedGroup.objects.filter(subAdminID=user.subAdminID).all()
    context = {
        'base': base,
        'company': company,
        'groups': groups,
        'companyHistory': companyHistory,
        'user': user
    }
    if request.method == 'POST':
        groupName = request.POST.get('groupName')
        companyName = request.POST.get('companyName')
        companyType = request.POST.get('companyType')
        
        if not groupName or not companyName or not companyType:
            messages.error(request, "Please fill all required fields.")
            return redirect(request.path)
        else:
            if user:
                
                group = UpdatedGroup.objects.filter(groupName=groupName, subAdminID=user.subAdminID).first()

                if group:
                    companyName_normalized = companyName.lower()
                    if UpdatedCompany.objects.filter(companyName__iexact=companyName_normalized, companyType=companyType).exists():
                        messages.error(request, "Company already exists.")
                        return redirect(request.path)
                    else:
                        company.companyName = companyName
                        company.companyType = companyType
                        company.groupID = group
                        company.userID = user
                        company.save()

                        companyHistory = HistoryCompany(
                            companyID=company, companyName=companyName, companyType=companyType, groupID=group,
                            userID=user, subAdminID=user.subAdminID, companyModifiedDate=company.companyModifiedDate
                        )
                        companyHistory.save()

                        messages.success(request, "Company updated successfully.")
                        return redirect(request.path)
                else:
                    messages.error(request, "Group not found.")
                    return redirect(request.path)
                
    return render(request, 'company/updateCompany.html', context)
    
def updateGroup(request, groupID):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
            
    group = UpdatedGroup.objects.get(groupID=groupID)
    groupHistory = HistoryGroup.objects.filter(groupID=groupID).all().order_by('-groupModifiedDate')
    context = {
        'base': base,
        'group': group,
        'user': user,
        'groupHistory': groupHistory
    }

    if request.method == 'POST':
        groupName = request.POST.get('groupName')
        
        if not groupName:
            messages.error(request, "Group name cannot be empty.")
            return redirect(request.path)
        else:
            if user:
                groupName_normalized = groupName.lower()
                # Check if the group already exists with the new name
                if UpdatedGroup.objects.filter(groupName__iexact=groupName_normalized).exists():
                    messages.error(request, "Group already exists.")
                    return redirect(request.path)
                
                group.groupName = groupName
                group.userID = user
                group.subAdminID = user.subAdminID
                group.save()

                groupHistory = HistoryGroup(
                    groupID=group, groupName=groupName, userID=user,
                    subAdminID=user.subAdminID, groupModifiedDate=group.groupModifiedDate
                )
                groupHistory.save()

                messages.success(request, "Group updated successfully.")
                return redirect(request.path)

    return render(request, 'group/updateGroup.html', context)
    
def updateClient(request, clientID):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    client = UpdatedClient.objects.get(clientID=clientID)
    clientHistory = HistoryClient.objects.filter(clientID=clientID).all().order_by('-clientModifiedDate')
    
    context = {
        'base': base,
        'client': client,
        'clientHistory': clientHistory,
        'user': user
    }

    if request.method == 'POST':
        clientName = request.POST.get('clientName')
        clientPhone = request.POST.get('clientPhone')

        # Check if all fields are filled
        if not all([clientName, clientPhone]):
            messages.error(request, "Please fill all required fields.")
            return redirect(request.path)

        # 1. Name validation: only letters and spaces
        if not re.match(r'^[A-Za-z\s]+$', clientName):
            messages.error(request, "Client name can only contain letters and spaces.")
            return redirect(request.path)

        # 2. Phone number validation: exactly 10 digits
        if not re.match(r'^\d{10}$', clientPhone):
            messages.error(request, "Phone number must be exactly 10 digits.")
            return redirect(request.path)

        if user:
            if client:
                # Check if the phone number or email already exists
                if UpdatedClient.objects.filter(clientPhone=clientPhone).exists() and UpdatedClient.objects.filter(clientName=clientName).exists():
                    messages.error(request, "Phone number already exists.")
                    return redirect(request.path)

                # Update client details
                client.clientName = clientName
                client.userID = user
                client.clientPhone = clientPhone
                client.save()

                # Update client history
                clientHistory = HistoryClient(
                    clientID=client, clientName=clientName, companyID=client.companyID,
                    userID=user, clientPhone=clientPhone,
                    subAdminID=user.subAdminID, clientModifiedDate=client.clientModifiedDate
                )
                clientHistory.save()

                messages.success(request, "Client updated successfully.")
                return redirect(request.path)
            else:
                messages.error(request, "Company not found.")
                return redirect(request.path)

    return render(request, 'client/updateClient.html', context)

def updateWork(request, formID):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
    
    # Retrieve the work record for the current sub-admin and specified formID.
    work = get_object_or_404(Work, formID=formID, subAdminID=user.subAdminID)
    historyWork = HistoryWork.objects.filter(formID=work.formID).all()
    
    context = {
        'base': base,
        'historyWork': historyWork,
        'work': work
    }
    
    if request.method == 'POST':
        formNo = request.POST.get('formNo')
        matter = request.POST.get('matter')
        filingDays = request.POST.get('filingDays')
        
        # Prepare form data to repopulate form in case of errors.
        form_data = {
            'formNo': formNo,
            'matter': matter,
            'filingDays': filingDays,
        }
        
        # Validate that all required fields are provided.
        if not all([formNo, matter, filingDays]):
            messages.error(request, "Please fill all required fields.")
        # Check that filingDays is numeric.
        elif not filingDays.isdigit():
            messages.error(request, "Filing days must be a number.")
            form_data['filingDays'] = ''
        # Check if formNo already exists for the current sub-admin (excluding this record)
        elif Work.objects.filter(formNo=formNo, subAdminID=user.subAdminID).exclude(formID=work.formID).exists():
            messages.error(request, "Form number already exists.")
            context['form_data'] = form_data
            return render(request, 'work/updateWork.html', context)
        else:
            try:
                # Update the work record
                work.formNo = formNo
                work.matter = matter
                work.filingDays = int(filingDays)
                work.modifiedBy = user
                work.save()

                historyWork = HistoryWork(
                    formID=work,
                    subAdminID=user.subAdminID,  # Assumes 'user' is an instance of SignUp
                    formNo=formNo,
                    matter=matter,
                    filingDays=int(filingDays),
                    modifiedBy=user,
                    modifiedDate=work.modifiedDate
                )
                historyWork.save()

                messages.success(request, "Work updated successfully.")
                return HttpResponseRedirect(reverse('listWork'))
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        
        # If errors exist, re-render the form with the posted data.
        context['form_data'] = form_data
        return render(request, 'work/updateWork.html', context)
    
    else:
        # For GET requests, prepopulate the form with the existing data.
        form_data = {
            'formNo': work.formNo,
            'matter': work.matter,
            'filingDays': work.filingDays,
            'formID': work.formID
        }
        context['form_data'] = form_data
        return render(request, 'work/updateWork.html', context)

def updatePendingWork(request, pendingWorkID):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
    
    # Retrieve companies, forms, and users for the form dropdowns
    companies = UpdatedCompany.objects.filter(subAdminID=user.subAdminID).all()
    forms = Work.objects.filter(subAdminID=user.subAdminID).all()
    users = UpdatedUser.objects.filter(subAdminID=user.subAdminID, isActive="True").all()

    # Retrieve the pending work record ensuring it belongs to the current sub-admin.
    pending_work = get_object_or_404(PendingWork, pendingWorkID=pendingWorkID, subAdminID=user.subAdminID)
    historyPendingWork = HistoryPendingWork.objects.filter(pendingWorkID=pending_work.pendingWorkID).all()
    
    context = {
        'base': base,
        'companies': companies,
        'forms': forms,
        'users': users,
        'user': user,
        'pending_work': pending_work,
        'historyPendingWork': historyPendingWork
    }
    
    
    
    if request.method == 'POST':
        # Get data from POST request
        form_no             = request.POST.get('formNo')             # form number from the input
        company_name        = request.POST.get('companyName')          # company name from the input
        event_date          = request.POST.get('eventDate')
        actual_due_date     = request.POST.get('actualDueDate')
        cutOffTime          = request.POST.get('cutOffTime')           # number field used to calculate internal due date
        srnNo_input         = request.POST.get('srnNo', '')
        internal_due_date   = request.POST.get('internalDueDate')
        user_id_str         = request.POST.get('userID')
        status              = request.POST.get('status')
        srn_date_input      = request.POST.get('srnDate', '')
        amt_input           = request.POST.get('amt', '')
        remark              = request.POST.get('remark')
        billing             = request.POST.get('billing')
        fees                = request.POST.get('fees', '')
        
        # For checkboxes, assume "on" if checked.
        isArchived = 'isArchived' in request.POST
        isPinned   = 'isPinned' in request.POST
        
        company = UpdatedCompany.objects.filter(companyName=company_name, subAdminID=user.subAdminID).first()
        groupName = company.groupID.groupName
        # Prepare form data to repopulate form in case of error

        form_data = request.POST.copy()
        form_data['groupName'] = groupName
        
        # Check required fields (optional fields are not included here)
        if not all([form_no, company_name, event_date, actual_due_date, 
                    cutOffTime, user_id_str, status, billing]):
            messages.error(request, "Please fill all required fields.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
        
        # Helper functions to parse optional date and amount fields.
        def parse_date(date_str):
            if date_str:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        def parse_amount(amt_str):
            try:
                return float(amt_str) if amt_str else None
            except ValueError:
                return None

        srnDate = parse_date(srn_date_input)
        amt = parse_amount(amt_input)
        fees = parse_amount(fees)
        
        # Fetch foreign key objects:
        try:
            # Look up the Work record based on formNo and current sub-admin.
            work_instance = Work.objects.get(formNo=form_no, subAdminID=user.subAdminID)
        except Work.DoesNotExist:
            messages.error(request, "Work record not found.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
        
        try:
            # Look up the company by companyName and current sub-admin.
            company_instance = UpdatedCompany.objects.get(companyName=company_name, subAdminID=user.subAdminID)
        except UpdatedCompany.DoesNotExist:
            messages.error(request, "Company record not found.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
        
        try:
            # Look up the UpdatedUser record using the provided userID.
            updated_user_instance = UpdatedUser.objects.filter(userName=user_id_str, subAdminID=user.subAdminID).first()
        except UpdatedUser.DoesNotExist:
            messages.error(request, "User record not found.")
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
        
        try:
            # Update the pending work record with new values.
            pending_work.formID           = work_instance
            pending_work.companyID        = company_instance
            pending_work.eventDate        = event_date
            pending_work.actualDueDate    = actual_due_date
            pending_work.cutOffTime       = cutOffTime
            pending_work.internalDueDate  = internal_due_date
            pending_work.userID           = updated_user_instance
            pending_work.status           = status
            pending_work.srnNo            = srnNo_input
            pending_work.srnDate          = srnDate
            pending_work.amt              = amt
            pending_work.remark           = remark
            pending_work.billing          = billing
            pending_work.fees          = fees
            pending_work.isArchived       = isArchived
            pending_work.isPinned         = isPinned
        
            pending_work.save()

            history_pending_work = HistoryPendingWork(
                pendingWorkID=pending_work,
                subAdminID=user.subAdminID,
                formID=work_instance,
                companyID=company_instance,
                eventDate=event_date,
                cutOffTime=cutOffTime,
                internalDueDate=internal_due_date,
                actualDueDate=actual_due_date,
                userID=updated_user_instance,
                status=status,
                srnNo=srnNo_input,
                srnDate=srnDate,
                amt=amt,
                remark=remark,
                billing=billing,
                fees=fees,
                isArchived=isArchived,
                isPinned=isPinned,
                modifiedDate=pending_work.modifiedDate
            )
            history_pending_work.save()
            messages.success(request, "Pending work updated successfully.")
            return HttpResponseRedirect(reverse('listPendingWork'))
        except Exception as e:
            messages.error(request, f"Error updating pending work: {e}")
            context['form_data'] = form_data
            return render(request, 'pendingWork/updatePendingWork.html', context)
    
    else:
        # For GET request, prepopulate form_data with existing pending_work values.
        form_data = {
            'pendingWorkID': pending_work.pendingWorkID,
            'formNo': pending_work.formID.formNo if pending_work.formID else "",
            'matter': pending_work.formID.matter if pending_work.formID else "",
            'filingDays': pending_work.formID.filingDays if pending_work.formID else "",
            'companyName': pending_work.companyID.companyName if pending_work.companyID else "",
            'groupName': pending_work.companyID.groupID.groupName if pending_work.companyID and hasattr(pending_work.companyID, 'groupID') else "",
            'eventDate': pending_work.eventDate,
            'actualDueDate': pending_work.actualDueDate,
            'cutOffTime': pending_work.cutOffTime,
            'srnNo': pending_work.srnNo,
            'internalDueDate': pending_work.internalDueDate,
            'userName': pending_work.userID.userName if pending_work.userID else "",
            'status': pending_work.status,
            'srnDate': pending_work.srnDate,
            'amt': pending_work.amt,
            'remark': pending_work.remark,
            'billing': pending_work.billing,
            'fees': pending_work.fees,
            'isArchived': pending_work.isArchived,
            'isPinned': pending_work.isPinned 
        }
        context['form_data'] = form_data
        return render(request, 'pendingWork/updatePendingWork.html', context)
        
def updateAnnual(request, annualFilingID):
    user = getUser(request).get('user')
    base = getUser(request).get('base')
    companies = UpdatedCompany.objects.filter(subAdminID=user.subAdminID).all()

    # Retrieve the existing AnnualFiling record, ensuring it belongs to the current sub-admin.
    annual_filing = get_object_or_404(AnnualFiling, annualFilingID=annualFilingID, subAdminID=user.subAdminID)
    historyAnnualFiling = HistoryAnnualFiling.objects.filter(annualFilingID=annual_filing.annualFilingID)

    
    context = {
        'base': base,
        'user': user,
        'companies': companies,
        'historyAnnualFiling': historyAnnualFiling,
        'annual_filing': annual_filing
    }
    
    
    if request.method == 'POST':
        # Retrieve data from POST request
        company_name       = request.POST.get('companyName')
        financialYear      = request.POST.get('financialYear')
        
        statusDPT3         = request.POST.get('statusDPT3', 'N/A')
        srnNoDPT3          = request.POST.get('srnNoDPT3')
        srnDateDPT3_str    = request.POST.get('srnDateDPT3')
        amtDPT3_str        = request.POST.get('amtDPT3')
        
        statusMGT14        = request.POST.get('statusMGT14', 'N/A')
        srnNoMGT14         = request.POST.get('srnNoMGT14')
        srnDateMGT14_str   = request.POST.get('srnDateMGT14')
        amtMGT14_str       = request.POST.get('amtMGT14')
        
        statusAOC4         = request.POST.get('statusAOC4', 'N/A')
        srnNoAOC4          = request.POST.get('srnNoAOC4')
        srnDateAOC4_str    = request.POST.get('srnDateAOC4')
        amtAOC4_str        = request.POST.get('amtAOC4')
        
        statusMGT7         = request.POST.get('statusMGT7', 'N/A')
        srnNoMGT7          = request.POST.get('srnNoMGT7')
        srnDateMGT7_str    = request.POST.get('srnDateMGT7')
        amtMGT7_str        = request.POST.get('amtMGT7')
        
        statusForm11       = request.POST.get('statusForm11', 'N/A')
        srnNoForm11        = request.POST.get('srnNoForm11')
        srnDateForm11_str  = request.POST.get('srnDateForm11')
        amtForm11_str      = request.POST.get('amtForm11')
        
        statusForm8        = request.POST.get('statusForm8', 'N/A')
        srnNoForm8         = request.POST.get('srnNoForm8')
        srnDateForm8_str   = request.POST.get('srnDateForm8')
        amtForm8_str       = request.POST.get('amtForm8')
        
        isArchived = 'isArchived' in request.POST
        isPinned    = 'isPinned' in request.POST

        # Validate required fields (adjust as needed)
        if not company_name or not financialYear:
            messages.error(request, "Company name and Financial Year are required.")
            context['form_data'] = request.POST
            return render(request, 'annualFiling/updateAnnual.html', context)

        # Look up the company record using the provided company name and current sub-admin.
        try:
            company = UpdatedCompany.objects.get(companyName=company_name, subAdminID=user.subAdminID)
        except UpdatedCompany.DoesNotExist:
            messages.error(request, "Company not found.")
            context['form_data'] = request.POST
            return render(request, 'annualFiling/updateAnnual.html', context)

        # Helper functions to parse dates and amounts.
        def parse_date(date_str):
            if date_str:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        def parse_amount(amt_str):
            try:
                return float(amt_str) if amt_str else 0.0
            except ValueError:
                return 0.0

        srnDateDPT3   = parse_date(srnDateDPT3_str)
        srnDateMGT14  = parse_date(srnDateMGT14_str)
        srnDateAOC4   = parse_date(srnDateAOC4_str)
        srnDateMGT7   = parse_date(srnDateMGT7_str)
        srnDateForm11 = parse_date(srnDateForm11_str)
        srnDateForm8  = parse_date(srnDateForm8_str)

        amtDPT3   = parse_amount(amtDPT3_str)
        amtMGT14  = parse_amount(amtMGT14_str)
        amtAOC4   = parse_amount(amtAOC4_str)
        amtMGT7   = parse_amount(amtMGT7_str)
        amtForm11 = parse_amount(amtForm11_str)
        amtForm8  = parse_amount(amtForm8_str)

        try:
            # Update the AnnualFiling record with new values
            annual_filing.companyID     = company
            annual_filing.financialYear = financialYear
            
            annual_filing.statusDPT3    = statusDPT3
            annual_filing.srnNoDPT3     = srnNoDPT3
            annual_filing.srnDateDPT3   = srnDateDPT3
            annual_filing.amtDPT3       = amtDPT3
            
            annual_filing.statusMGT14   = statusMGT14
            annual_filing.srnNoMGT14    = srnNoMGT14
            annual_filing.srnDateMGT14  = srnDateMGT14
            annual_filing.amtMGT14      = amtMGT14
            
            annual_filing.statusAOC4    = statusAOC4
            annual_filing.srnNoAOC4     = srnNoAOC4
            annual_filing.srnDateAOC4   = srnDateAOC4
            annual_filing.amtAOC4       = amtAOC4
            
            annual_filing.statusMGT7    = statusMGT7
            annual_filing.srnNoMGT7     = srnNoMGT7
            annual_filing.srnDateMGT7   = srnDateMGT7
            annual_filing.amtMGT7       = amtMGT7
            
            annual_filing.statusForm11  = statusForm11
            annual_filing.srnNoForm11   = srnNoForm11
            annual_filing.srnDateForm11 = srnDateForm11
            annual_filing.amtForm11     = amtForm11
            
            annual_filing.statusForm8   = statusForm8
            annual_filing.srnNoForm8    = srnNoForm8
            annual_filing.srnDateForm8  = srnDateForm8
            annual_filing.amtForm8      = amtForm8
            
            annual_filing.isArchived    = isArchived
            annual_filing.isPinned      = isPinned
            annual_filing.modifiedBy = user
            annual_filing.save()

            historyaf = HistoryAnnualFiling(
                annualFilingID = annual_filing,
                subAdminID     = user.subAdminID,
                companyID      = company,
                financialYear  = financialYear,
                
                statusDPT3     = statusDPT3,
                srnNoDPT3      = srnNoDPT3,
                srnDateDPT3    = srnDateDPT3,
                amtDPT3        = amtDPT3,
                
                statusMGT14    = statusMGT14,
                srnNoMGT14     = srnNoMGT14,
                srnDateMGT14   = srnDateMGT14,
                amtMGT14       = amtMGT14,
                
                statusAOC4     = statusAOC4,
                srnNoAOC4      = srnNoAOC4,
                srnDateAOC4    = srnDateAOC4,
                amtAOC4        = amtAOC4,
                
                statusMGT7     = statusMGT7,
                srnNoMGT7      = srnNoMGT7,
                srnDateMGT7    = srnDateMGT7,
                amtMGT7        = amtMGT7,
                
                statusForm11   = statusForm11,
                srnNoForm11    = srnNoForm11,
                srnDateForm11  = srnDateForm11,
                amtForm11      = amtForm11,
                
                statusForm8    = statusForm8,
                srnNoForm8     = srnNoForm8,
                srnDateForm8   = srnDateForm8,
                amtForm8       = amtForm8,
                
                isArchived     = isArchived,
                isPinned       = isPinned,
                modifiedBy=user,
                modifiedDate   = annual_filing.modifiedDate
            )
            historyaf.save()
            messages.success(request, "Annual Filing updated successfully!")
            return HttpResponseRedirect(reverse('listAnnual'))
        except Exception as e:
            messages.error(request, f"Error updating Annual Filing: {e}")
            context['form_data'] = request.POST
            return render(request, 'annualFiling/updateAnnual.html', context)
    
    else:
        # For GET, prepopulate form_data with existing record values.
        form_data = {
            'annualFilingID': annual_filing.annualFilingID,
            'companyName': annual_filing.companyID.companyName if annual_filing.companyID else "",
            'groupName': annual_filing.companyID.groupID.groupName if annual_filing.companyID else "",
            'financialYear': annual_filing.financialYear,
            
            'statusDPT3': annual_filing.statusDPT3,
            'srnNoDPT3': annual_filing.srnNoDPT3,
            'srnDateDPT3': annual_filing.srnDateDPT3,
            'amtDPT3': annual_filing.amtDPT3,
            
            'statusMGT14': annual_filing.statusMGT14,
            'srnNoMGT14': annual_filing.srnNoMGT14,
            'srnDateMGT14': annual_filing.srnDateMGT14,
            'amtMGT14': annual_filing.amtMGT14,
            
            'statusAOC4': annual_filing.statusAOC4,
            'srnNoAOC4': annual_filing.srnNoAOC4,
            'srnDateAOC4': annual_filing.srnDateAOC4,
            'amtAOC4': annual_filing.amtAOC4,
            
            'statusMGT7': annual_filing.statusMGT7,
            'srnNoMGT7': annual_filing.srnNoMGT7,
            'srnDateMGT7': annual_filing.srnDateMGT7,
            'amtMGT7': annual_filing.amtMGT7,
            
            'statusForm11': annual_filing.statusForm11,
            'srnNoForm11': annual_filing.srnNoForm11,
            'srnDateForm11': annual_filing.srnDateForm11,
            'amtForm11': annual_filing.amtForm11,
            
            'statusForm8': annual_filing.statusForm8,
            'srnNoForm8': annual_filing.srnNoForm8,
            'srnDateForm8': annual_filing.srnDateForm8,
            'amtForm8': annual_filing.amtForm8,
            
            'isArchived': annual_filing.isArchived,
            'isPinned': annual_filing.isPinned
        }
        context['form_data'] = form_data
        return render(request, 'annualFiling/updateAnnual.html', context)


# All Delete Function are here
def deleteDSC(request):
    if request.method == 'POST':
        dscIDs = request.POST.getlist('dscIDs')
        confirmation = request.POST.get('deleteDSC')
        if confirmation:
            if not dscIDs:
                messages.error(request, "No DSCs selected for deletion.")
            else:
                count, _ = UpdatedDSC.objects.filter(dscID__in=dscIDs).delete()
                if count > 0:
                    messages.success(request, f"Deleted DSC(s) successfully.")
                else:
                    messages.error(request, "No DSCs were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    
    return redirect('listDSC')

def deleteCompany(request):
    if request.method == 'POST':
        companyIDs = request.POST.getlist('companyIDs')
        confirmation = request.POST.get('deleteCompany')
        if confirmation:
            if not companyIDs:
                messages.error(request, "No companies selected for deletion.")
            else:
                companies_to_delete = UpdatedCompany.objects.filter(companyID__in=companyIDs)
                undeletable_companies = []

                for company in companies_to_delete:
                    # Check if there are clients or DSCs associated with the company
                    has_clients = UpdatedClient.objects.filter(companyID=company.companyID).exists()
                    has_dscs = UpdatedDSC.objects.filter(companyID=company.companyID).exists()

                    if has_clients or has_dscs:
                        undeletable_companies.append(company.companyID)

                if undeletable_companies:
                    messages.error(request,f"Phone Book / DSC exist. You can't delete Company.")
                else:
                    count, _ = companies_to_delete.delete()
                    if count > 0:
                        messages.success(request, "Selected company(ies) deleted successfully.")
                    else:
                        messages.error(request, "No companies were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    
    return redirect('listCompany')

def deleteGroup(request):
    if request.method == 'POST':
        groupIDs = request.POST.getlist('groupIDs')
        confirmation = request.POST.get('deleteGroup')
        if confirmation:
            if not groupIDs:
                messages.error(request, "No groups selected for deletion.")
            else:
                groups_to_delete = UpdatedGroup.objects.filter(groupID__in=groupIDs)
                undeletable_groups = []

                for group in groups_to_delete:
                    # Check if there are companies, clients, or DSCs associated with the group
                    has_companies = UpdatedCompany.objects.filter(groupID=group.groupID).exists()
                    has_clients = UpdatedClient.objects.filter(companyID__groupID=group.groupID).exists()
                    has_dscs = UpdatedDSC.objects.filter(companyID__groupID=group.groupID).exists()

                    if has_companies or has_clients or has_dscs:
                        undeletable_groups.append(group.groupID)

                if undeletable_groups:
                    messages.error(request, "Company / Phone Book / DSC exist. You can't delete Group.")
                else:
                    count, _ = groups_to_delete.delete()
                    if count > 0:
                        messages.success(request, "Selected group(s) deleted successfully.")
                    else:
                        messages.error(request, "No groups were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    
    return redirect('listGroup')

def deleteClient(request):
    if request.method == 'POST':
        clientIDs = request.POST.getlist('clientIDs')
        confirmation = request.POST.get('deleteClient')
        if confirmation:
            if not clientIDs:
                messages.error(request, "No clients selected for deletion.")
            else:
                count, _ = UpdatedClient.objects.filter(clientID__in=clientIDs).delete()
                if count > 0:
                    messages.success(request, f"Deleted client(s) successfully.")
                else:
                    messages.error(request, "No clients were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    
    return redirect('listClient')

def deleteWork(request):
    if request.method == 'POST':
        formIDs = request.POST.getlist('formIDs')  # List of selected work IDs
        confirmation = request.POST.get('deleteWork')  # Confirmation checkbox/button
        
        if confirmation:
            if not formIDs:
                messages.error(request, "No work records selected for deletion.")
            else:
                # Check if any of the selected work has pending work attached
                has_pending = PendingWork.objects.filter(formID__in=formIDs).exists()

                if has_pending:
                    messages.error(request, "Some Pending Work exist. You can't delete work.")
                else:
                    # If no pending work is attached, proceed with deletion
                    count, _ = Work.objects.filter(formID__in=formIDs).delete()
                    if count > 0:
                        messages.success(request, f"Deleted {count} work record(s) successfully.")
                    else:
                        messages.error(request, "No work records were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")

    return redirect('listWork')

def deletePendingWork(request):
    if request.method == 'POST':
        pendingWorkIDs = request.POST.getlist('pendingWorkIDs')
        confirmation = request.POST.get('deletePendingWork')
        if confirmation:
            if not pendingWorkIDs:
                messages.error(request, "No pending work records selected for deletion.")
            else:
                count, _ = PendingWork.objects.filter(pendingWorkID__in=pendingWorkIDs).delete()
                if count > 0:
                    messages.success(request, f"Deleted {count} pending work record(s) successfully.")
                else:
                    messages.error(request, "No pending work records were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    return redirect('listPendingWork')

def deleteAnnual(request):
    if request.method == 'POST':
        annualFilingIDs = request.POST.getlist('annualFilingIDs')
        confirmation = request.POST.get('deleteAnnual')
        if confirmation:
            if not annualFilingIDs:
                messages.error(request, "No annual filing records selected for deletion.")
            else:
                count, _ = AnnualFiling.objects.filter(annualFilingID__in=annualFilingIDs).delete()
                if count > 0:
                    messages.success(request, f"Deleted {count} annual filing record(s) successfully.")
                else:
                    messages.error(request, "No annual filing records were deleted. Please try again.")
        else:
            messages.error(request, "Deletion not confirmed.")
    return redirect('listAnnual')


# All Other Function are here
def updatePassword(request):
    user = getUser(request).get('user')
    subAdmin = getUser(request).get('subAdmin')
    superAdmin = getUser(request).get('superAdmin')
    base = getUser(request).get('base')
    
    if subAdmin:
        user = None

    if request.method == 'POST':
        oldPassword = request.POST.get('oldPassword')
        newPassword = request.POST.get('newPassword')
        confirmPassword = request.POST.get('confirmPassword')

        # Password validation function
        def validate_new_password(password):
            return (len(password) >= 8 and
                    re.search(r'[A-Za-z]', password) and
                    re.search(r'\d', password) and
                    re.search(r'[@$!%*?&#]', password))

        # Check if it's a user or subAdmin updating their password
        if user:
            if check_password(oldPassword, user.userPassword):
                if newPassword == confirmPassword:
                    if validate_new_password(newPassword):
                        user.userPassword = make_password(newPassword)
                        user.save()
                        messages.success(request, 'Password updated successfully!')
                    else:
                        messages.error(request, "New password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
                else:
                    messages.error(request, 'New password and confirmation do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        elif subAdmin:
            if check_password(oldPassword, subAdmin.subAdminPassword):
                if newPassword == confirmPassword:
                    if validate_new_password(newPassword):
                        subAdmin.subAdminPassword = make_password(newPassword)
                        subAdmin.save()
                        messages.success(request, 'Password updated successfully!')
                    else:
                        messages.error(request, "New password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
                else:
                    messages.error(request, 'New password and confirmation do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        elif superAdmin:
            if check_password(oldPassword, superAdmin.superAdminPassword):
                if newPassword == confirmPassword:
                    if validate_new_password(newPassword):
                        superAdmin.superAdminPassword = make_password(newPassword)
                        superAdmin.save()
                        messages.success(request, 'Password updated successfully!')
                    else:
                        messages.error(request, "New password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).")
                else:
                    messages.error(request, 'New password and confirmation do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')

    context = {
        'base': base,
        'subAdmin': subAdmin
    }
    return render(request, 'password/updatePassword.html', context)

def feedBack(request):
    user = getUser(request).get('user')
    base = getUser(request).get('base')

    context = {
        'base': base,
        'user': user,
    }
    if request.method == 'POST':
        rating = request.POST.get('rating')
        feedbackText = request.POST.get('feedBack')

        Feedback.objects.create(rating=rating, feedbackText=feedbackText, subAdminID=user.subAdminID)
        messages.success(request, "Your feedback is submited successfully.")
        return redirect(request.path) 

    return render(request, 'contactUs/feedBack.html', context)

def fetchGroupName(request):
    if request.method == 'POST':
        companyName = request.POST.get('companyName')  # Corrected typo
        user = getUser(request).get('user')

        subAdminID = user.subAdminID

        try:
            company = UpdatedCompany.objects.get(companyName=companyName, subAdminID=subAdminID)
            groupName = company.groupID.groupName
            companyType = company.companyType
            try: 
                client = UpdatedClient.objects.get(subAdminID=subAdminID, companyID=company.companyID)
                clientName = client.clientName
                clientPhone = client.clientPhone
            except:
                clientName = ''
                clientPhone = ''

            response_data = {
                'status': 'success',
                'group_name': groupName,
                'client_name': clientName,
                'client_phone': clientPhone,
                'company_type': companyType,  
                'exists': True
            }
    
        except UpdatedCompany.DoesNotExist:
            response_data = {
                'status': 'error',
                'message': 'Company name does not exist',
                'exists': False
            }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def fetchFormDetails(request):
    if request.method == 'POST':
        formNo = request.POST.get('formNo')  # Corrected typo
        user = getUser(request).get('user')

        subAdminID = user.subAdminID

        try:
            form = Work.objects.get(formNo=formNo, subAdminID=subAdminID)
            
            matter = form.matter
            filingDays = form.filingDays

            response_data = {
                'status': 'success',
                'form_matter': matter, 
                'filing_days': filingDays,
                'exists': True
            }
        except Work.DoesNotExist:
            response_data = {
                'status': 'error',
                'message': 'Form does not exist',
                'exists': False
            }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

import urllib.parse
def send_whatsapp_message(phone_number, client_name, status, person):
    # Clean the phone number (remove spaces and '+' signs)
    phone_number = phone_number.replace('+', '').replace(' ', '')
    
    if status == 'IN':
        # Create the message
        message = f"Hello {client_name}, your DSC is received {status} from {person}"
    elif status == 'OUT':
        # Create the message
        message = f"Hello {client_name}, your DSC is delivered {status} to {person}"
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # Generate the WhatsApp URL
    whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
    
    # Return the WhatsApp URL to be used in the frontend or backend
    return whatsapp_url

