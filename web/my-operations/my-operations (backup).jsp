<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8"%>

<%@page import="nist.bfrl.vcctl.database.User" %>

<%
User user = (User)request.getSession().getAttribute("user");
String username = user.getName();
%>

<table>
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td>
            <h4>
                Operations executed by <%=username%>:
            </h4>
        </td>
    </tr>
    <tr>
        <td>
            <hr>
        </td>
    </tr>
</table>
<br>

<%@page import="nist.bfrl.vcctl.database.*" %>
<%@page import="java.util.List" %>
<%@page import="java.text.*" %>


<%@taglib prefix="html" uri="/WEB-INF/struts-html.tld" %>


<html:form action="/database/operation/edit.do" >
    <html:hidden property="editop" />
    <html:hidden property="opname" />
    
    <script language="javascript">
        function set(ctrl)
        {
        document.forms[0].editop.value=ctrl.value;
        document.forms[0].opname.value=ctrl.name;
        }
        
        function updateOperations() {
        document.forms[0].opname.value="update";
        document.forms[0].editop.value="all";
        document.forms[0].submit();
        }
    </script>
    
    <%
    List recent_ops = OperationDatabase.getOperationsByStatusForUser("running", "start",username);
    Format formatter;
    formatter = new SimpleDateFormat("d MMM yyyy HH:mm:ss");
    String bgcolor;
    %>
    
    <b>Running Operations</b>
    <table class="operations-table" >
        <%  if (recent_ops.size() < 1) {   %>      
        <br><em>No running operations</em>
        <%  } else {                       %>
        <thead  >
            <tr>
                <th>
                    Name
                </th>
                <th>
                    Type
                </th>
                <th>
                    Time started
                </th>
                <th>
                    
                </th>
            </tr>
        </thead>
        <% } %>
        
        <%
        /* Greens for running operations */
        for (int i=0; i<recent_ops.size(); i++) {
        Operation op_i = (Operation)recent_ops.get(i);
        if (i%2 == 0) {
            bgcolor="#99ff99";
        } else {
            bgcolor="#66ff66";
        }
        %>
        <tr bgcolor="<%=bgcolor%>">
            <td>
                <%=op_i.getName() %>
            </td>
            <td>
                <%=op_i.getType()%>
            </td>
            <td>
                <%=formatter.format(op_i.getStart()) %>
            </td>
            <td>
                <html:submit styleClass="tablebutton" property="<%=op_i.getName()%>" onclick="set(this)">
                    view
                </html:submit>
            </td>
            <td>
                <html:submit styleClass="tablebutton" property="<%=op_i.getName()%>" onclick="set(this)">
                    cancel
                </html:submit>
            </td>
        </tr>
        <%
        }
        %>
    </table>
    <br>
    
    
    <%
    recent_ops = OperationDatabase.getOperationsByStatusForUser("finished", "finish",username);
    %>
    <b>Finished Operations</b>
    <table class="operations-table" >
        
        <%
        if (recent_ops.size() < 1) {
        %>      
        <br><em>No finished operations </em>
        <%
        } else {
        %>
        <thead  >
            <tr>
                <th>
                    Name
                </th>
                <th>
                    Type
                </th>
                <th>
                    Time finished
                </th>
                <th>
                    
                </th>
                <th>
                    
                </th>
            </tr>
        </thead>
        <% } %>
        <%
        /* Blues for finished ops */
        for (int i=0; i<recent_ops.size(); i++) {
        Operation op_i = (Operation)recent_ops.get(i);
        if (i%2 == 0) {
            bgcolor="#99ccff";
        } else {
            bgcolor="#ccffff";
        }
        %>
        <tr bgcolor="<%=bgcolor%>">
            <td>
                <%=op_i.getName() %>
            </td>
            <td>
                <%=op_i.getType()%>
            </td>
            <td>
                <%=formatter.format(op_i.getFinish()) %>
            </td>
            <td>
                <html:submit styleClass="tablebutton" property="<%=op_i.getName()%>" onclick="set(this)">
                    view
                </html:submit>
            </td>
            <td>
                <html:submit styleClass="tablebutton" property="<%=op_i.getName()%>" onclick="set(this)">
                    delete
                </html:submit>
            </td>
        </tr>
        <%
        }
        %>
    </table>
    <br>
    
    <%
    recent_ops = OperationDatabase.getOperationsByStatusForUser("cancelled", "finish", username);
    %>
    <b>Cancelled Operations</b>
    <table class="operations-table" >
        
        <%
        if (recent_ops.size() < 1) {
        %>      
        <br><em>No cancelled operations </em>
        <%
        } else {
        %>
        <thead  >
            <tr>
                <th>
                    Name
                </th>
                <th>
                    Type
                </th>
                <th>
                    Time finished
                </th>
                <th>
                    
                </th>
                <th>
                    
                </th>
            </tr>
        </thead>
        <% } %>
        <%
        
        // Red for cancelled operations
        
        for (int i=0; i<recent_ops.size(); i++) {
        Operation op_i = (Operation)recent_ops.get(i);
        if (i%2 == 0) {
            bgcolor="#ff9999";
        } else {
            bgcolor="#ffcccc";
        }
        %>
        <tr bgcolor="<%=bgcolor%>">
            <td>
                <%=op_i.getName() %>
            </td>
            <td>
                <%=op_i.getType()%>
            </td>
            <td>
                <%=formatter.format(op_i.getFinish()) %>
            </td>
            <td>
                <html:submit styleClass="tablebutton" property="<%=op_i.getName()%>" onclick="set(this)">
                    view
                </html:submit>
            </td>
            <td>
                <html:submit styleClass="tablebutton" property="<%=op_i.getName()%>" onclick="set(this)">
                    delete
                </html:submit>
            </td>
        </tr>
        <%
        }
        %>
    </table>
    <br>
    
    
    <%
    recent_ops = OperationDatabase.getOperationsByStatusForUser(username, "queued", "queue");
    %>
    <b>Queued Operations</b>
    <table class="operations-table" >
        <%
        if (recent_ops.size() < 1) {
        %>      
        <br><em> No queued operations </em>
        <%
        } else {
        %>
        <thead  >
            <tr>
                <th>
                    Name
                </th>
                <th>
                    Type
                </th>
                <th>
                    Time queued
                </th>
            </tr>
        </thead>
        <% }
    // Yellow for queued operations
    for (int i=0; i<recent_ops.size(); i++) {
        Operation op_i = (Operation)recent_ops.get(i);
        if (i%2 == 0) {
            bgcolor="#ffff99";
        } else {
            bgcolor="#ffffcc";
        }
        %>
        <tr bgcolor="<%=bgcolor%>">
            <td>
                <%=op_i.getName() %>
            </td>
            <td>
                <%=op_i.getType()%>
            </td>
            <td>
                <%=formatter.format(op_i.getQueue()) %>
            </td>
            <td>
                <html:submit styleClass="tablebutton" property="<%=op_i.getName()%>" onclick="set(this)">
                    dequeue
                </html:submit>
            </td>
        </tr>
        <% } %>
    </table>
</html:form>

<script language="javascript">
    setTimeout("updateOperations()", 15000);
</script>
