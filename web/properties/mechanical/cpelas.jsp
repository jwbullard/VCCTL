<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8"%>

<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>

<jsp:useBean id="operation_database" class="nist.bfrl.vcctl.database.OperationDatabaseBean"
             scope="page" />

<table>
    <tr>
        <td>
            <h4>
                Calculate cement paste elastic moduli
            </h4>
        </td>
    </tr>
    <tr>
        <td>
            <hr>
        </td>
    </tr>
</table>


<html:form action="/properties/mechanical/cpelas.do">
    <table>
        <tr>
            <td>
                Name of hydrated microstructure:
            </td>
            <td>
                <html:select property="microstructure">
                    <html:options name="operation_database" property="hydrated_microstructures" />
                </html:select>
            </td>
        </tr>
        <tr>
            <td>
                Resolve spatial variations in moduli:
            </td>
            <td>
                <html:checkbox property="resolve_spatial_variations" />
            </td>
        </tr>
        <tr>
            <td>
                Early age option:
            </td>
            <td>
                <html:checkbox property="early_age_option" />
            </td>
        </tr>
        <tr>
            <td>
                <br>
            </td>
        </tr>
        <tr>
            <td>
                <html:submit />
            </td>
        </tr>
    </table>
</html:form>