<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>

<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>

<%@page import="nist.bfrl.vcctl.database.Operation" %>
<html:xhtml />

<script type="text/javascript">
	selectTab(4);
	$('subtab-menu').hide();
	$('top-border').show();
</script>

<h3>My Operations</h3>
<html:form action="/my-operations/editMyOperations.do">
	<html:hidden property='operationToCancel' />
	<html:hidden property='operationToDelete' />
	<html:hidden property="operationToView" />
		<fieldset>
		<legend><b>Queued operations</b></legend>
		<bean:size id="queuedOperationsNumber" name="myOperationsForm" property="queuedOperations" />
		<% if (queuedOperationsNumber > 0) { %>
			<table class="list-table">
				<thead>
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
				<tbody>
					<logic:iterate name="myOperationsForm" property="queuedOperations" id="queuedOperation" indexId="ind">
						<% if (ind%2 == 0) { %>
							<tr class="even-queued-operation">
						<% } else { %>
							<tr class="odd-queued-operation">
						<% } %>
							<td>
								<a href="javascript:document.forms[0].operationToView.value='<%=((Operation)queuedOperation).getName()%>'; ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=view_operation',document.forms[0],'content');" id="view-queued-operation_<%=ind%>"><bean:write name="queuedOperation" property="name"/></a>
							</td>
							<td>
								<bean:write name="queuedOperation" property="type"/>
							</td>
							<td>
								<bean:write name="queuedOperation" property="formattedQueuedTime"/>
							</td>
							<td>
								<a href="javascript:document.forms[0].operationToDelete.value='<%=((Operation)queuedOperation).getName()%>'; ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=delete_operation',document.forms[0],'content');" id="delete-queued-operation_<%=ind%>">Delete</a>
							</td>
						</tr>
					</logic:iterate>
				</tbody>
			</table>
		<% } else { %>
			No queued operations
		<% } %>
	</fieldset>
        <fieldset>
		<legend><b>Running operations</b></legend>
		<bean:size id="runningOperationsNumber" name="myOperationsForm" property="runningOperations" />
                 <% if (runningOperationsNumber > 0) { %>
			<table class="list-table">
				<thead>
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
					</tr>
				</thead>
				<tbody>
					<logic:iterate name="myOperationsForm" property="runningOperations" id="runningOperation" indexId="ind">
						<% if (ind%2 == 0) { %>
							<tr class="even-running-operation">
						<% } else { %>
							<tr class="odd-running-operation">
						<% } %>
							<td>
								<a href="javascript:document.forms[0].operationToView.value='<%=((Operation)runningOperation).getName()%>'; ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=view_operation',document.forms[0],'content');" id="view-running-operation_<%=ind%>"><bean:write name="runningOperation" property="name"/></a>
							</td>
							<td>
								<bean:write name="runningOperation" property="type"/>
							</td>
							<td>
								<bean:write name="runningOperation" property="formattedStartTime"/>
							</td>
							<td>
								<a href="javascript:document.forms[0].operationToCancel.value='<%=((Operation)runningOperation).getName()%>'; ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=cancel_operation',document.forms[0],'content');" id="delete-running-operation_<%=ind%>">Cancel</a>
							</td>
						</tr>
					</logic:iterate>
				</tbody>
			</table>
		<% } 
                
                else { %>
			No running operations
		<% } %>
	</fieldset>
	<fieldset>
		<legend><b>Finished operations</b></legend>
		<bean:size id="finishedOperationsNumber" name="myOperationsForm" property="finishedOperations" />
		<% if (finishedOperationsNumber > 0) { %>
			<table class="list-table">
				<thead>
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
							Time finished
						</th>
					</tr>
				</thead>
				<tbody>
					<logic:iterate name="myOperationsForm" property="finishedOperations" id="finishedOperation" indexId="ind">
						<% if (ind%2 == 0) { %>
							<tr class="even-finished-operation">
						<% } else { %>
							<tr class="odd-finished-operation">
						<% } %>
							<td>
								<a href="javascript:document.forms[0].operationToView.value='<%=((Operation)finishedOperation).getName()%>'; ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=view_operation',document.forms[0],'content');" id="view-finished-operation_<%=ind%>"><bean:write name="finishedOperation" property="name"/></a>
							</td>
							<td>
								<bean:write name="finishedOperation" property="type"/>
							</td>
							<td>
								<bean:write name="finishedOperation" property="formattedStartTime"/>
							</td>
							<td>
								<bean:write name="finishedOperation" property="formattedFinishTime"/>
							</td>
							<td>
								<a href="javascript:document.forms[0].operationToDelete.value='<%=((Operation)finishedOperation).getName()%>'; ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=delete_operation',document.forms[0],'content');" id="delete-finished-operation_<%=ind%>">Delete</a>
							</td>
						</tr>
					</logic:iterate>
				</tbody>
			</table>
		<% } else { %>
			No finished operations
		<% } %>
	</fieldset>

	<fieldset>
		<legend><b>Cancelled operations</b></legend>
		<bean:size id="cancelledOperationsNumber" name="myOperationsForm" property="cancelledOperations" />
		<% if (cancelledOperationsNumber > 0) { %>
			<table class="list-table">
				<thead>
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
							Time cancelled
						</th>
					</tr>
				</thead>
				<tbody>
					<logic:iterate name="myOperationsForm" property="cancelledOperations" id="cancelledOperation" indexId="ind">
						<% if (ind%2 == 0) { %>
							<tr class="even-cancelled-operation">
						<% } else { %>
							<tr class="odd-cancelled-operation">
						<% } %>
							<td>
								<a href="javascript:document.forms[0].operationToView.value='<%=((Operation)cancelledOperation).getName()%>'; ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=view_operation',document.forms[0],'content');" id="view-cancelled-operation_<%=ind%>"><bean:write name="cancelledOperation" property="name"/></a>
							</td>
							<td>
								<bean:write name="cancelledOperation" property="type"/>
							</td>
							<td>
								<bean:write name="cancelledOperation" property="formattedStartTime"/>
							</td>
							<td>
								<bean:write name="cancelledOperation" property="formattedFinishTime"/>
							</td>
							<td>
								<a href="javascript:document.forms[0].operationToDelete.value='<%=((Operation)cancelledOperation).getName()%>'; ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=delete_operation',document.forms[0],'content');" id="delete-cancelled-operation_<%=ind%>">Delete</a>
							</td>
						</tr>
					</logic:iterate>
				</tbody>
			</table>
		<% } else { %>
			No cancelled operations
		<% } %>
	</fieldset>
</html:form>
<script language="javascript">
	var timer;
	clearTimeout(timer);
	timer = setInterval("if (document.forms[0].name == 'myOperationsForm') { ajaxUpdateContainerWithStrutsAction('<%=request.getContextPath()%>/my-operations/editMyOperations.do?action=update',document.forms[0],'myOperationsForm');}", 15000);
</script>
