<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java"%>

<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>

<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
        <link rel="stylesheet" href="<%=request.getContextPath()%>/css/default-layout.css" type="text/css"/>
		<script src="<%=request.getContextPath()%>/script/prototype.js" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/checkings.js" type="text/javascript"></script>
		<title>
			Virtual Cement and Concrete Testing Laboratory 9.5 - New User
		</title>
    </head>

    <body>
		<html:form action="/admin/register.do" focus="userName" onsubmit="return checkUserInfo();">
			<fieldset>
				<legend class="user-info-legend">Username:</legend>
				<div class="problem_msg" id="name_alreadyTaken" style="display:none">
					The username is already taken by another user.
				</div>
				<div class="problem_msg" id="invalid_name" style="display:none">
					The username is not valid. Try to use another name, with no punctuation marks. Some names are reserved and can not be used, too.
				</div>
				<div class="problem_msg" id="badSize_name" style="display:none">
					The username must be between 3 and 32 characters.
				</div>
				Enter your desired username: <html:text property="userName" size="24" onblur="checkUserName(this);" />
				<img id="name_OK_img" src="<%=request.getContextPath()%>/images/ok.gif" alt="" style="display:none" />
				<img id="name_problem_img" src="<%=request.getContextPath()%>/images/problem.gif" alt="" style="display:none" />
			</fieldset>
			<fieldset>
				<legend class="user-info-legend">Password:</legend>
				<div class="problem_msg" id="passwords_dontMatch" style="display:none">
					The passwords do not match.
				</div>
				<div class="problem_msg" id="passwords_empty" style="display:none">
					The password section is incomplete
				</div>
				<img class="matching_img" id="passwords_OK_img" src="<%=request.getContextPath()%>/images/ok.gif" alt="" style="display:none" />
				<img class="matching_img" id="passwords_problem_img" src="<%=request.getContextPath()%>/images/problem.gif" alt="" style="display:none" />
				Enter your password: <html:password property="password" size="24" />
				Confirm your password: <input type="password" id="confirmPasword" name="confirmPasword" onblur="checkPasswords();" />
                                <html:hidden property="email" value="defaultEmail@nowhwere.org"/>
                                <input type="hidden" id="confirmEmail" name="confirmEmail" value="defaultEmail@nowhwere.org" />
			</fieldset>
			<!-- <fieldset> 
				<legend class="user-info-legend">Email address:</legend>
				<div class="problem_msg" id="email_alreadyTaken" style="display:none">
					The email address is already in use by another member.
				</div>
				<div class="problem_msg" id="invalid_email_address" style="display:none">
					The email address you entered is invalid (ex: name@domain.com) or contains illegal characters.
				</div>
				<div class="problem_msg" id="email_adresses_dontMatch" style="display:none">
					The email addresses do not match.
				</div>
				<img class="matching_img" id="emails_OK_img" src="<%=request.getContextPath()%>/images/ok.gif" alt="" style="display:none" />
				<img class="matching_img" id="emails_problem_img" src="<%=request.getContextPath()%>/images/problem.gif" alt="" style="display:none" />
                                Enter your email address: <input type="hidden" property="email" value="defaultEmail@nowhwere.org" onblur="checkEmailValidity(this);" />
				Confirm your email address: <input type="hidden" id="confirmEmail" name="confirmEmail" value="defaultEmail@nowhwere.org" onblur="checkEmails();" />
                             </fieldset> -->
			<html:submit value="Submit" />
		</html:form>
    </body>
</html>
