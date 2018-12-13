<%@page import="nist.bfrl.vcctl.database.*"
>%<%@page import="nist.bfrl.vcctl.util.Constants"
%><%@page import="java.util.*"
%><%@page import = "java.io.*"
%><%@page contentType="image/gif"
%><jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabase" scope="session" />
<%

  String cemName;

  if ( request.getParameter("cemName") != null )
  {

    cemName = request.getParameter("cemName");

    try
    {
       // get the image from the database
       byte[] imgData = cement_database.getGif(Constants.CEMENT_TABLE_NAME,cemName) ;
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
