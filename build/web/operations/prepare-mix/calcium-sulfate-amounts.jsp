<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>

<%@page import="nist.bfrl.vcctl.operation.microstructure.*" %>

<%
String spanid;
%>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<table>
    <tr>
        <th>
            Sulfate form
        </th>
        <th>
            PSD/characteristics file
        </th>
        <th>
            Mass fraction
        </th>
        <th>
            Volume fraction
        </th>
    </tr>
    <% String sulfate[] = {"Dihydrate", "Hemihydrate", "Anhydrite"};
    for (int i=0; i<sulfate.length; i++) {
        String propname; %>
    <tr>
        <td>
            <%=sulfate[i]%>
        </td>
        <td>
            <% propname = Phase.property(sulfate[i])+"_psd";%>
            <span id=<%=propname%>>
                <html:select  style="width:20ex" property="<%=propname%>">
					<html:options name="cement_database" property="psds" />
                </html:select>
            </span>
        </td>
        <td>
            <% propname = Phase.property(sulfate[i])+"_massfrac";%>
            <span id="<%=propname%>"><html:text size="6" property="<%=propname%>" onchange="onChangeSulfateMassFraction(this)" /></span>
        </td>
        <td>
            <% propname = Phase.property(sulfate[i])+"_volfrac";%>
            <span id="<%=propname%>"><html:text size="6" property="<%=propname%>" onchange="onChangeSulfateVolumeFraction(this)" /></span>
        </td>
    </tr>
    <% } %>
</table>
