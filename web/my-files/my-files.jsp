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
        urls[0] = "<%=request.getContextPath()%>/lab-materials/initializeMyMicrostructureFiles.do";
        urls[1] = "<%=request.getContextPath()%>/lab-materials/initializeMyAggregateFiles.do";
        urls[2] = "<%=request.getContextPath()%>/lab-materials/initializeMyHydrationFiles.do";
        urls[3] = "<%=request.getContextPath()%>/lab-materials/initializeMyMechanicalFiles.do";
        urls[4] = "<%=request.getContextPath()%>/lab-materials/initializeMyTransportFiles.do";
        createSubTabsMenu(titles,ids,urls);
    }
    $('subtab-menu').show();
    $('top-border').hide();
    selectSubTab(0);
</script>

<h3>My Microstructure Files</h3>
<html:form action="/my-files/editMyMicrostructureFiles.do">
	<bean:size id="microstructureOperationsNumber" name="myFilesForm" property="microstructureOperations" />
	<logic:greaterThan name="microstructureOperationsNumber" value="0">
		<fieldset id="microstructure-operations">
			<legend><b>Microstructure operations</b></legend>
			<nested:iterate name="myFilesForm" property="microstructureOperations" indexId="ind">
				<nested:define id="operationName" property="name" />
				<nested:equal property="viewOperation" value="false">
					<fieldset id="microstructure-operation_<%=ind%>" class="collapsed">
						<legend class="collapsable-title collapsed"><a onclick="collapseExpand('microstructure-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
							<div class="collapsable-content collapsed">
				</nested:equal>
				<nested:equal property="viewOperation" value="true">
					<fieldset id="microstructure-operation_<%=ind%>" class="expanded">
						<legend class="collapsable-title expanded"><a onclick="collapseExpand('microstructure-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
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
												<a href="javascript:viewFile('microstructureOperations(<%=operationName%>).filesList[<%=i%>]','show-microstructure-file-content_<%=ind%>_<%=i%>','to-reload');" id="show-microstructure-file-content_<%=ind%>_<%=i%>">Show</a>
												<nested:link action="/my-files/downloadFile.do" property="linkParameters">Export</nested:link>
												<nested:hidden property="viewContent" />
												<nested:equal property="viewContent" value="true">
													<nested:equal property="type" value="text">
														<div id="microstructure-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area"><nested:write property="formattedContent" filter="false"/></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<nested:define id="sliceName" property="sliceName" />
														<div id="microstructure-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"><nested:link action="/my-files/viewImage.do" property="linkParameters"><img src="/vcctl/image/<%=sliceName%>" /></nested:link></div>
													</nested:equal>
												</nested:equal>
												<nested:equal property="viewContent" value="false">
													<nested:equal property="type" value="text">
														<div id="microstructure-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area hidden"></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<div id="microstructure-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"></div>
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
									Export all files for this operation in one zip file: <nested:link action="/my-files/downloadFile.do" paramId="operation" paramProperty="name" styleClass="link"><nested:write property="zipArchiveName" /></nested:link>
								</logic:greaterThan>
							</nested:notEmpty>
						</div>
					</fieldset>
			</nested:iterate>
		</fieldset>
	</logic:greaterThan>
	<bean:size id="aggregateOperationsNumber" name="myFilesForm" property="aggregateOperations" />
	<logic:greaterThan name="aggregateOperationsNumber" value="0">
		<fieldset id="aggregate-operations">
			<legend><b>Aggregate operations</b></legend>
			<nested:iterate name="myFilesForm" property="aggregateOperations" indexId="ind">
				<nested:define id="operationName" property="name" />
				<nested:equal property="viewOperation" value="false">
					<fieldset id="aggregate-operation_<%=ind%>" class="collapsed">
						<legend class="collapsable-title collapsed"><a onclick="collapseExpand('aggregate-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
							<div class="collapsable-content collapsed">
				</nested:equal>
				<nested:equal property="viewOperation" value="true">
					<fieldset id="aggregate-operation_<%=ind%>" class="expanded">
						<legend class="collapsable-title expanded"><a onclick="collapseExpand('aggregate-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
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
												<a href="javascript:viewFile('aggregateOperations(<%=operationName%>).filesList[<%=i%>]','show-aggregate-file-content_<%=ind%>_<%=i%>','to-reload');" id="show-aggregate-file-content_<%=ind%>_<%=i%>">Show</a>
												<nested:link action="/my-files/downloadFile.do" property="linkParameters">Export</nested:link>
												<nested:hidden property="viewContent" />
												<nested:equal property="viewContent" value="true">
													<nested:equal property="type" value="text">
														<div id="aggregate-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area"><nested:write property="formattedContent" filter="false"/></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<nested:define id="sliceName" property="sliceName" />
														<div id="aggregate-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"><nested:link action="/my-files/viewImage.do" property="linkParameters"><img src="/vcctl/image/<%=sliceName%>" /></nested:link></div>
													</nested:equal>
												</nested:equal>
												<nested:equal property="viewContent" value="false">
													<nested:equal property="type" value="text">
														<div id="aggregate-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area hidden"></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<div id="aggregate-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"></div>
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
									Export all files for this operation in one zip file: <nested:link action="/my-files/downloadFile.do" paramId="operation" paramProperty="name" styleClass="link"><nested:write property="zipArchiveName" /></nested:link>
								</logic:greaterThan>
							</nested:notEmpty>
						</div>
					</fieldset>
			</nested:iterate>
		</fieldset>
	</logic:greaterThan>
	<bean:size id="hydrationOperationsNumber" name="myFilesForm" property="hydrationOperations" />
	<logic:greaterThan name="hydrationOperationsNumber" value="0">
		<fieldset id="hydration-operations">
			<legend><b>Hydration operations</b></legend>
			<nested:iterate name="myFilesForm" property="hydrationOperations" indexId="ind">
				<nested:define id="operationName" property="name" />
				<nested:equal property="viewOperation" value="false">
					<fieldset id="hydration-operation_<%=ind%>" class="collapsed">
						<legend class="collapsable-title collapsed"><a onclick="collapseExpand('hydration-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
							<div class="collapsable-content collapsed">
				</nested:equal>
				<nested:equal property="viewOperation" value="true">
					<fieldset id="hydration-operation_<%=ind%>" class="expanded">
						<legend class="collapsable-title expanded"><a onclick="collapseExpand('hydration-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
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
												<a href="javascript:viewFile('hydrationOperations(<%=operationName%>).filesList[<%=i%>]','show-hydration-file-content_<%=ind%>_<%=i%>','to-reload');" id="show-hydration-file-content_<%=ind%>_<%=i%>">Show</a>
												<nested:link action="/my-files/downloadFile.do" property="linkParameters">Export</nested:link>
												<nested:hidden property="viewContent" />
												<nested:equal property="viewContent" value="true">
													<nested:equal property="type" value="text">
														<div id="hydration-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area"><nested:write property="formattedContent" filter="false"/></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<nested:define id="sliceName" property="sliceName" />
														<div id="hydration-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"><nested:link action="/my-files/viewImage.do" property="linkParameters"><img src="/vcctl/image/<%=sliceName%>" /></nested:link></div>
													</nested:equal>
												</nested:equal>
												<nested:equal property="viewContent" value="false">
													<nested:equal property="type" value="text">
														<div id="hydration-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area hidden"></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<div id="hydration-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"></div>
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
									Export all files for this operation in one zip file: <nested:link action="/my-files/downloadFile.do" paramId="operation" paramProperty="name" styleClass="link"><nested:write property="zipArchiveName" /></nested:link>
								</logic:greaterThan>
							</nested:notEmpty>
						</div>
					</fieldset>
			</nested:iterate>
		</fieldset>
	</logic:greaterThan>
	<bean:size id="elasticModuliOperationsNumber" name="myFilesForm" property="elasticModuliOperations" />
	<logic:greaterThan name="elasticModuliOperationsNumber" value="0">
		<fieldset id="elastic-moduli-operations">
			<legend><b>Mechanical properties operations</b></legend>
			<nested:iterate name="myFilesForm" property="elasticModuliOperations" indexId="ind">
				<nested:define id="operationName" property="name" />
				<nested:equal property="viewOperation" value="false">
					<fieldset id="elastic-moduli-operation_<%=ind%>" class="collapsed">
						<legend class="collapsable-title collapsed"><a onclick="collapseExpand('elastic-moduli-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
							<div class="collapsable-content collapsed">
				</nested:equal>
				<nested:equal property="viewOperation" value="true">
					<fieldset id="elastic-moduli-operation_<%=ind%>" class="expanded">
						<legend class="collapsable-title expanded"><a onclick="collapseExpand('elastic-moduli-operation_<%=ind%>');"><nested:write property="name" /></a></legend>
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
												<a href="javascript:viewFile('elasticModuliOperations(<%=operationName%>).filesList[<%=i%>]','show-elastic-moduli-file-content_<%=ind%>_<%=i%>','to-reload');" id="show-elastic-moduli-file-content_<%=ind%>_<%=i%>">Show</a>
												<nested:link action="/my-files/downloadFile.do" property="linkParameters">Export</nested:link>
												<nested:hidden property="viewContent" />
												<nested:equal property="viewContent" value="true">
													<nested:equal property="type" value="text">
														<div id="elastic-moduli-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area"><nested:write property="formattedContent" filter="false"/></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<nested:define id="sliceName" property="sliceName" />
														<div id="elastic-moduli-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"><nested:link action="/my-files/viewImage.do" property="linkParameters"><img src="/vcctl/image/<%=sliceName%>" /></nested:link></div>
													</nested:equal>
												</nested:equal>
												<nested:equal property="viewContent" value="false">
													<nested:equal property="type" value="text">
														<div id="elastic-moduli-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area hidden"></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<div id="elastic-moduli-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"></div>
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
									Export all files for this operation in one zip file: <nested:link action="/my-files/downloadFile.do" paramId="operation" paramProperty="name" styleClass="link"><nested:write property="zipArchiveName" /></nested:link>
								</logic:greaterThan>
							</nested:notEmpty>
						</div>
					</fieldset>
			</nested:iterate>
		</fieldset>
	</logic:greaterThan>
        <bean:size id="transportFactorOperationsNumber" name="myFilesForm" property="transportFactorOperations" />
	<logic:greaterThan name="transportFactorOperationsNumber" value="0">
		<fieldset id="transport-factor-operations">
			<legend><b>Transport properties operations</b></legend>
			<nested:iterate name="myFilesForm" property="transportFactorOperations" indexId="ind">
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
												<a href="javascript:viewFile('transportFactorOperations(<%=operationName%>).filesList[<%=i%>]','show-transport-factor-file-content_<%=ind%>_<%=i%>','to-reload');" id="show-transport-factor-file-content_<%=ind%>_<%=i%>">Show</a>
												<nested:link action="/my-files/downloadFile.do" property="linkParameters">Export</nested:link>
												<nested:hidden property="viewContent" />
												<nested:equal property="viewContent" value="true">
													<nested:equal property="type" value="text">
														<div id="transport-factor-file-content_<%=ind%>_<%=i%>" class="to-reload file-text-area"><nested:write property="formattedContent" filter="false"/></div>
													</nested:equal>
													<nested:equal property="type" value="image">
														<nested:define id="sliceName" property="sliceName" />
														<div id="transport-factor-file-content_<%=ind%>_<%=i%>" class="to-reload file-image"><nested:link action="/my-files/viewImage.do" property="linkParameters"><img src="/vcctl/image/<%=sliceName%>" /></nested:link></div>
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
									Export all files for this operation in one zip file: <nested:link action="/my-files/downloadFile.do" paramId="operation" paramProperty="name" styleClass="link"><nested:write property="zipArchiveName" /></nested:link>
								</logic:greaterThan>
							</nested:notEmpty>
						</div>
					</fieldset>
			</nested:iterate>
		</fieldset>
	</logic:greaterThan>
</html:form>