<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>


<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>

<div class="report">
    <logic:present name="generateMicrostructureForm" >
        <table>
            <caption>
                Microstructure Common Properties:
            </caption>
            <tr>
                <td colspan="2">
                    <hr>
                </td>
            </tr>
            <tr>
                <td>
                    File name:
                </td>
                <td>
                    <bean:write name="initmicro" property="filename" />
                </td>
            </tr>
            <tr>
                <td>
                    Dimensions:
                </td>
                <td>
                    <bean:write name="generateMicrostructureForm" property="x_dim"/>x<bean:write name="generateMicrostructureForm" property="y_dim"/>x<bean:write name="generateMicrostructureForm" property="z_dim"/> pixels
                </td>
            </tr>
            <tr>
                <td>
                    Resolution:
                </td>
                <td>
                    <bean:write name="generateMicrostructureForm" property="resolution"/> microns
                </td>
            </tr>
            <tr>
                <td>
                    RNG seed:
                </td>
                <td>
                    <bean:write name="generateMicrostructureForm" property="rng_seed"/>
                </td>
            </tr>
            <tr>
                <td>
                    Real shapes:
                </td>
                <td>
                    <bean:write name="generateMicrostructureForm" property="real_shapes"/>
                </td>
            </tr>
            <logic:equal name="generateMicrostructureForm" property="real_shapes" value="true">
                <tr>
                    <td>
                        Shape set:
                    </td>
                    <td>
                        <bean:write name="generateMicrostructureForm" property="shape_set"/>
                    </td>
                </tr>
            </logic:equal>
            <tr>
                <td>
                    Flocculation:
                </td>
                <td>
                    <logic:equal name="generateMicrostructureForm" property="flocs" value="0">
                        no
                    </logic:equal>
                    <logic:notEqual name="generateMicrostructureForm" property="flocs" value="0">
                        <bean:write name="generateMicrostructureForm" property="flocs"/> flocs
                    </logic:notEqual>
                </td>
            </tr>
            <tr>
                <td>
                    Dispersion distance:
                </td>
                <td>
                <bean:write name="generateMicrostructureForm" property="dispersion_distance"/>
                </td>
            </tr>
        </table>
    </logic:present>
</div>

