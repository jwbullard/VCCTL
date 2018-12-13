<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8"%>

<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>


<%
   String imgpath = request.getContextPath();
   imgpath = imgpath + "/images/";
   imgpath += (String)request.getSession().getAttribute("gif");
%>

<img src="<%=imgpath%>" height="200" width="200" border="4" />

    <h4 align="center"><bean:write name="createSampleForm" property="psd_file"/></h4>

<b>Sample file properties:</b><br><hr>
Name:
<b>
<bean:write name="createSampleForm" property="name"/>
</b><br>
Dimensions: 
<bean:write name="createSampleForm" property="x_dim"/> x
<bean:write name="createSampleForm" property="y_dim"/> x
<bean:write name="createSampleForm" property="z_dim"/><br>
Resolution:
<bean:write name="createSampleForm" property="resolution"/> microns/pixel<br>

<logic:equal name="createSampleForm" property="aggregate_thickness" value="0">
No aggregate present.
</logic:equal>
<logic:notEqual name="createSampleForm" property="aggregate_thickness" value="0">
Aggregate thickness: 
<bean:write name="createSampleForm" property="aggregate_thickness"/>
pixels
</logic:notEqual>
<br><hr>

<html:form action="/operation/hydrate/edit-sample.do" focus="wcratio"  >
Target water/cement ratio: <html:text size="12"  property="wcratio" /><br>
Actual water/cement ratio:
<html:text readonly="true" size="12" maxlength="6" property="actual_wcratio" styleClass="read-only-input" />
<br><br>
<html:submit value="Create Sample File" />
</html:form>
