<%-- 
    Document   : my-transport-files
    Created on : Oct 28, 2011, 2:11:21 PM
    Author     : bullard
--%>

<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>

<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>
<%@taglib uri="http://struts.apache.org/tags-nested" prefix="nested" %>

<html:xhtml />

<script type="text/javascript">
    selectTab(5);
    if (!$$('#subtabs-right ul')[0] || !$$('#subtabs-right ul')[0].hasChildNodes() || ($$('#subtabs-right ul li')[0] && $$('#subtabs-right ul li')[0].id != "my-microstructure-files")) {
        var titles = new Array();
        titles[0] = "Microstructure";
        titles[1] = "Aggregate";
        titles[2] = "Hydration";
        titles[3] = "Mechanical Properties";
        titles[4] = "Transport Properties";
        var ids = new Array();
        ids[0] = "my-microstructure-files";
        ids[1] = "my-aggregate-files";
        ids[2] = "my-hydration-files";
        ids[3] = "my-mechanical-files";
        ids[4] = "my-transport-files";
        var urls = new Array();
        urls[0] = "<%=request.getContextPath()%>/my-files/initializeMyMicrostructureFiles.do";
        urls[1] = "<%=request.getContextPath()%>/my-files/initializeMyAggregateFiles.do";
        urls[2] = "<%=request.getContextPath()%>/my-files/initializeMyHydrationFiles.do";
        urls[3] = "<%=request.getContextPath()%>/my-files/initializeMyMechanicalFiles.do";
        urls[4] = "<%=request.getContextPath()%>/my-files/initializeMyTransportFiles.do";
        createSubTabsMenu(titles,ids,urls);
    }
    $('subtab-menu').show();
    $('top-border').hide();
    selectSubTab(4);
</script>

<h3>My Transport Properties Files</h3>
<html:form action="/my-files/editMyTransportFiles.do">
        <bean:size id="transportFactorOperationsNumber" name="myTransportFilesForm" property="transportFactorOperations" />
	<logic:greaterThan name="transportFactorOperationsNumber" value="0">
		<fieldset id="transport-factor-operations">
			<legend><b>Transport properties operations</b></legend>
			<nested:iterate name="myTransportFilesForm" property="transportFactorOperations" indexId="ind">
				<nested:define id="operationName" property="name" />
				<nested:equal property="viewOperation" value="false">
					<fieldset id="transport-factor-operation_<%=ind%>" class="collapsed">
						<legend class="collapsable-title collapsed"><a onclick="collapseExpand('transport-factor-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
							<div class="collapsable-content collapsed">
				</nested:equal>
				<nested:equal property="viewOperation" value="true">
					<fieldset id="transport-factor-operation_<%=ind%>" class="expanded">
						<legend class="collapsable-title expanded"><a onclick="collapseExpand('transport-factor-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
						<div class="collapsable-content expanded">
				</nested:equal>
							<table class="list-table">
								<thead>
									<tr>
										<th>
											File
										</th>
										<th>
											Description
										</th>
										<th>
											Content
										</th>
									</tr>
								</thead>
								<nested:notEmpty property="filesList">
									<nested:iterate property="filesList" indexId="i">
										<% if (i%2 == 0) { %>
										<tr class="even-file">
										<% } else { %>
										<tr class="odd-file">
											<% } %>
											<td>
												<nested:write property="name"/>
											</td>
											<td>
												<nested:write property="description"/>
											</td>
											<td>
												<a href="javascript:viewTransportFile('transportFactorOperations(<%=operationName%>).filesList[<%=i%>]','show-transport-factor-file-content_<%=ind%>_<%=i%>','to-reload');" id="show-transport-factor-file-content_<%=ind%>_<%=i%>">Show</a>
												<nested:link action="/my-files/downloadTransportFile.do" property="linkParameters">Export</nested:link>
												<nested:hidden property="viewContent" />
												<nested:equal property="viewContent" value="true">
													<nested:equal property="type" value="text">
														<div id="transport-factor-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area"><nested:write property="formattedContent" filter="false"/></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<nested:define id="sliceName" property="sliceName" />
														<div id="transport-factor-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"><nested:link action="/my-files/viewImage.do" target="_blank" property="linkParameters"><img src="/vcctl/image/<%=sliceName%>" /></nested:link></div>
													</nested:equal>
												</nested:equal>
												<nested:equal property="viewContent" value="false">
													<nested:equal property="type" value="text">
														<div id="transport-factor-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area hidden"></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<div id="transport-factor-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"></div>
													</nested:equal>
												</nested:equal>
											</td>
										</tr>
									</nested:iterate>
								</nested:notEmpty>
							</table>
							<nested:notEmpty property="filesList">
								<nested:size id="filesNumber" property="filesList" />
								<logic:greaterThan name="filesNumber" value="0">
									Export all files for this operation in one zip file: <nested:link action="/my-files/downloadTransportFile.do" paramId="operation" paramProperty="name" styleClass="link"><nested:write property="zipArchiveName" /></nested:link>
								</logic:greaterThan>
							</nested:notEmpty>
						</div>
					</fieldset>
			</nested:iterate>
		</fieldset>
	</logic:greaterThan>
</html:form>
