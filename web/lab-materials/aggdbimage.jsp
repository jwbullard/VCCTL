<%-- 
    Document   : aggdbimage
    Created on : Feb 26, 2010, 5:10:51 PM
    Author     : bullard
--%>

<%@page import="nist.bfrl.vcctl.database.*" %>
<%@page import="nist.bfrl.vcctl.util.Constants" %>
<%@page import="java.util.*" %>
<%@ page import = "java.io.*" %>
<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabase" scope="page" />
<%

  String aggName;

  if ( request.getParameter("aggName") != null )
  {

    aggName = request.getParameter("aggName");

    try
    {
       // get the image from the database
       byte[] imgData = cement_database.getGif(Constants.AGGREGATE_TABLE_NAME,aggName) ;
       // display the image
       response.setContentType("image/gif");
       OutputStream o = response.getOutputStream();
       o.write(imgData);
       o.flush();
       o.close();
    }
    catch (Exception e)
    {
      e.printStackTrace();
      throw e;
    }
  }
%>
