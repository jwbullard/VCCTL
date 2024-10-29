<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java"%>
<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>

<html:html lang="en" xhtml="true">
    <head>
		<html:base/>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <link rel="stylesheet" href="<%=request.getContextPath()%>/css/default-layout.css" type="text/css"/>
		<title>
			Virtual Cement and Concrete Testing Laboratory 9.5
		</title>
    </head>
	<body>
		<html:form action="/admin/login.do" focus="userName">
			<fieldset>
				<legend class="user-info-legend">Connection</legend>
				Login: <html:text property="userName" size="24" />
				Password: <html:password property="password" size="24" />
				<html:submit value="Connect" />
			</fieldset>
		</html:form>
		<p>New user? <a href="<%=request.getContextPath()%>/pages/registration.jsp">Click here!</a></p>
    </body>
</html:html>
