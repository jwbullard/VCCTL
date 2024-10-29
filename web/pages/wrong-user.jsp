<%-- 
    Document   : wrong-user
    Created on : Jul 1, 2008, 3:41:29 PM
    Author     : borise
--%>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">
   
<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java"%>
<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<html lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<title>VCCTL 7</title>
         <link rel="stylesheet" href="<%=request.getContextPath()%>/css/default-layout.css" type="text/css"/>
</head>
<body>
	
         <div class="problem_msg" id="user_Invalid" >
	 Login is invalid.
	</div> 
         <p><a href="<%=request.getContextPath()%>/index.jsp">Sign in</a></p>
         
</body>
</html>
