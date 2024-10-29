<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">

<html lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<title>VCCTL 9</title>
         <link rel="stylesheet" href="<%=request.getContextPath()%>/css/default-layout.css" type="text/css"/>
</head>
<body>
	
         <div class="problem_msg" id="error_Message" >
	 You have a Derby database connection issue. Please make sure Derby is running.
         Here's the connection error message thrown by the Java DataBase Connector (JDBC):
	</div>
          
         <div class="problem_msg" id="error_Message" >
	 <%= session.getAttribute( "errorMessage" ) %>
	</div>
          <% session.removeAttribute("errorMessage");%>
          <p><a href="<%=request.getContextPath()%>/index.jsp">Sign in</a></p>
        
         
</body>
</html>