<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@page import="nist.bfrl.vcctl.operation.microstructure.*" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>

<%
String material[] = {"Silica fume", "CaCO3", "Free Lime"};
String checkboxName, addProp, propMassFrac, propName, propHTMLCode;
%>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<table>
    <tr>
        <th>
        </th>
        <th>
            PSD/characteristics file
        </th>
        <th>
            Mass Fraction
        </th>
        <th>
            Volume Fraction
        </th>
    </tr>
    <tr>
        <td>
            <span id="add_fly_ash">
                <html:hidden property="add_fly_ash" />
                <logic:equal name="mixingForm" property="add_fly_ash" value="true">
                    <input type="checkbox" name="add_fly_ash_checkbox" CHECKED onclick="addOrRemoveCementitiousMaterial(this.form,'fly_ash');" />Add Fly Ash
                </logic:equal>
                <logic:equal name="mixingForm" property="add_fly_ash" value="false">
                    <input type="checkbox" name="add_fly_ash_checkbox" onclick="addOrRemoveCementitiousMaterial(this.form,'fly_ash');" />Add Fly Ash
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="fly_ash_psd">
                <logic:equal name="mixingForm" property="add_fly_ash" value="true">
                    <html:select property="fly_ash_psd" onchange="retrieveURL('/e-vcctl/operation/prepareMix.do?action=change_flyash',this.form);" style="width:20ex">
                        <html:options name="cement_database" property="flyashs" />
                    </html:select>
                </logic:equal>
                <logic:equal name="mixingForm" property="add_fly_ash" value="false">
                    <html:select property="fly_ash_psd" onchange="retrieveURL('/e-vcctl/operation/prepareMix.do?action=change_flyash',this.form);" style="width:20ex" disabled="true">
                        <html:options name="cement_database" property="flyashs" />
                    </html:select>
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="fly_ash_massfrac">
                <logic:equal name="mixingForm" property="add_fly_ash" value="true">
                    <html:text size="6" property="fly_ash_massfrac" onchange="onChangeCementitiousMaterialMassFraction(this,'fly_ash')" />
                </logic:equal>
                <logic:equal name="mixingForm" property="add_fly_ash" value="false">
                    <html:text size="6" property="fly_ash_massfrac" onchange="onChangeCementitiousMaterialMassFraction(this,'fly_ash')" disabled="true" />
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="fly_ash_volfrac">
                <logic:equal name="mixingForm" property="add_fly_ash" value="true">
                    <html:text size="6" property="fly_ash_volfrac" onchange="onChangeCementitiousMaterialVolumeFraction(this,'fly_ash')" />
                </logic:equal>
                <logic:equal name="mixingForm" property="add_fly_ash" value="false">
                    <html:text size="6" property="fly_ash_volfrac" onchange="onChangeCementitiousMaterialVolumeFraction(this,'fly_ash')" disabled="true" />
                </logic:equal>
            </span>
        </td>
    </tr>
    <tr>
        <td>
            <span id="add_slag">
                <html:hidden property="add_slag" />
                <logic:equal name="mixingForm" property="add_slag" value="true">
                    <input type="checkbox" name="add_slag_checkbox" CHECKED onclick="addOrRemoveCementitiousMaterial(this.form,'slag');" />Add Slag
                </logic:equal>
                <logic:equal name="mixingForm" property="add_slag" value="false">
                    <input type="checkbox" name="add_slag_checkbox" onclick="addOrRemoveCementitiousMaterial(this.form,'slag');" />Add Slag
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="slag_psd">
                <logic:equal name="mixingForm" property="add_slag" value="true">
                    <html:select property="slag_psd" onchange="retrieveURL('/e-vcctl/operation/prepareMix.do?action=change_slag',this.form);" style="width:20ex">
                        <html:options name="cement_database" property="slags" />
                    </html:select>
                </logic:equal>
                <logic:equal name="mixingForm" property="add_slag" value="false">
                    <html:select property="slag_psd" onchange="retrieveURL('/e-vcctl/operation/prepareMix.do?action=change_slag',this.form);" style="width:20ex" disabled="true">
                        <html:options name="cement_database" property="slags" />
                    </html:select>
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="slag_massfrac">
                <logic:equal name="mixingForm" property="add_slag" value="true">
                    <html:text size="6" property="slag_massfrac" onchange="onChangeCementitiousMaterialMassFraction(this,'slag')" />
                </logic:equal>
                <logic:equal name="mixingForm" property="add_slag" value="false">
                    <html:text size="6" property="slag_massfrac" onchange="onChangeCementitiousMaterialMassFraction(this,'slag')" disabled="true" />
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="slag_volfrac">
                <logic:equal name="mixingForm" property="add_slag" value="true">
                    <html:text size="6" property="slag_volfrac" onchange="onChangeCementitiousMaterialVolumeFraction(this,'slag')" />
                </logic:equal>
                <logic:equal name="mixingForm" property="add_slag" value="false">
                    <html:text size="6" property="slag_volfrac" onchange="onChangeCementitiousMaterialVolumeFraction(this,'slag')" disabled="true" />
                </logic:equal>
            </span>
        </td>
    </tr>
    <tr>
        <td>
            <span id="add_inert_filler">
                <html:hidden property="add_inert_filler" />
                <logic:equal name="mixingForm" property="add_inert_filler" value="true">
                    <input type="checkbox" name="add_inert_filler_checkbox" CHECKED onclick="addOrRemoveCementitiousMaterial(this.form,'inert_filler');" />Add Inert Filler
                </logic:equal>
                <logic:equal name="mixingForm" property="add_inert_filler" value="false">
                    <input type="checkbox" name="add_inert_filler_checkbox" onclick="addOrRemoveCementitiousMaterial(this.form,'inert_filler');" />Add Inert Filler
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="inert_filler_psd">
                <logic:equal name="mixingForm" property="add_inert_filler" value="true">
                    <html:select property="inert_filler_psd" onchange="retrieveURL('/e-vcctl/operation/prepareMix.do?action=change_filler',this.form);" style="width:20ex">
                        <html:options name="cement_database" property="inert_fillers" />
                    </html:select>
                </logic:equal>
                <logic:equal name="mixingForm" property="add_inert_filler" value="false">
                    <html:select property="inert_filler_psd" onchange="retrieveURL('/e-vcctl/operation/prepareMix.do?action=change_filler',this.form);" style="width:20ex" disabled="true">
                        <html:options name="cement_database" property="inert_fillers" />
                    </html:select>
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="inert_filler_massfrac">
                <logic:equal name="mixingForm" property="add_inert_filler" value="true">
                    <html:text size="6" property="inert_filler_massfrac" onchange="onChangeCementitiousMaterialMassFraction(this,'inert_filler')" />
                </logic:equal>
                <logic:equal name="mixingForm" property="add_inert_filler" value="false">
                    <html:text size="6" property="inert_filler_massfrac" onchange="onChangeCementitiousMaterialMassFraction(this,'inert_filler')" disabled="true" />
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="inert_filler_volfrac">
                <logic:equal name="mixingForm" property="add_inert_filler" value="true">
                    <html:text size="6" property="inert_filler_volfrac" onchange="onChangeCementitiousMaterialVolumeFraction(this,'inert_filler')" />
                </logic:equal>
                <logic:equal name="mixingForm" property="add_inert_filler" value="false">
                    <html:text size="6" property="inert_filler_volfrac" onchange="onChangeCementitiousMaterialVolumeFraction(this,'inert_filler')" disabled="true" />
                </logic:equal>
            </span>
        </td>
    </tr>
    
    <% for (int i=0; i<material.length; i++) { %>
    <tr>
        <td>
            <% propName = Phase.property(material[i]);
            checkboxName = "add_" + propName + "_checkbox";
            addProp = "add_" + propName;
            propMassFrac = propName + "_massfrac";
			propHTMLCode = Phase.htmlCode(material[i]); %>
            <span id="<%=checkboxName%>">
                <html:hidden property="<%=addProp%>" />
                <logic:equal name="mixingForm" property="<%=addProp%>" value="true">
                    <input type="checkbox" name="<%=checkboxName%>" CHECKED onclick="addOrRemoveCementitiousMaterial(this.form,'<%=propName%>');" />Add <%=propHTMLCode%>
                </logic:equal>
                <logic:equal name="mixingForm" property="<%=addProp%>" value="false">
                    <input type="checkbox" name="<%=checkboxName%>" onclick="addOrRemoveCementitiousMaterial(this.form,'<%=propName%>');" />Add <%=propHTMLCode%>
                </logic:equal>
            </span>
        </td>
        <td>
            <% propName = Phase.property(material[i])+"_psd";%>
            <span id="<%=propName%>">
                <logic:equal name="mixingForm" property="<%=addProp%>" value="true">
                    <html:select  style="width:20ex" property="<%=propName%>">
                        <html:options name="cement_database" property="psds" />
                    </html:select>
                </logic:equal>
                <logic:equal name="mixingForm" property="<%=addProp%>" value="false">
                    <html:select  style="width:20ex" property="<%=propName%>" disabled="true">
                        <html:options name="cement_database" property="psds" />
                    </html:select>
                </logic:equal>
            </span>
        </td>
        <td>
            <span id="<%=propMassFrac%>">
                <logic:equal name="mixingForm" property="<%=addProp%>" value="true">
                    <html:text size="6" property="<%=propMassFrac%>" onchange="onChangeCementitiousMaterialMassFraction(this,'<%=propMassFrac%>')" />
                </logic:equal>
                <logic:equal name="mixingForm" property="<%=addProp%>" value="false">
                    <html:text size="6" property="<%=propMassFrac%>" onchange="onChangeCementitiousMaterialMassFraction(this,'<%=propMassFrac%>')" disabled="true" />
                </logic:equal>
            </span>
        </td>
        <td>
            <% propName = Phase.property(material[i])+"_volfrac";%>
            <span id="<%=propName%>">
                <logic:equal name="mixingForm" property="<%=addProp%>" value="true">
                    <html:text size="6" property="<%=propName%>" onchange="onChangeCementitiousMaterialVolumeFraction(this,'<%=propName%>')" />
                </logic:equal>
                <logic:equal name="mixingForm" property="<%=addProp%>" value="false">
                    <html:text size="6" property="<%=propName%>" onchange="onChangeCementitiousMaterialVolumeFraction(this,'<%=propName%>')" disabled="true" />
                </logic:equal>
            </span>
        </td>
    </tr>
    <% } %>
    <tr>
        <td colspan="4">
            <hr/>
        </td>
    </tr>
    <tr>
        <td colspan="2">Cement</td>
        <td>
            <span id="cement_massfrac"><html:text size="6" property="cement_massfrac" readonly="readonly" styleClass="read-only-input" /></span>
        </td>
        <td>
            <span id="cement_volfrac"><html:text size="6" property="cement_volfrac" readonly="readonly" styleClass="read-only-input" /></span>
        </td>
    </tr>
</table>
<span id="fly_ash_sg"><html:hidden property="fly_ash_sg" /></span>
<span id="slag_sg"><html:hidden property="slag_sg" /></span>
<span id="inert_filler_sg"><html:hidden property="inert_filler_sg" /></span>
