<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>

<%@page import="nist.bfrl.vcctl.database.*" %>
<%@page import="java.util.*" %>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<div id="random_seed">
    <span id="use_own_random_seed">
        <html:hidden property="use_own_random_seed" />
        <logic:equal name="mixingForm" property="use_own_random_seed" value="true">
            <input type="checkbox" name="use_own_random_seed_checkbox" CHECKED onclick="useOwnRandomSeed(this);" /> Use my own random number generator seed:
        </logic:equal>
        <logic:equal name="mixingForm" property="use_own_random_seed" value="false">
            <input type="checkbox" name="use_own_random_seed_checkbox" onclick="useOwnRandomSeed(this);" /> Use my own random number generator seed:
        </logic:equal>
    </span>
    <span id="rng_seed">
        <logic:equal name="mixingForm" property="use_own_random_seed" value="true">
            <html:text property="rng_seed" size="5" />
        </logic:equal>
        <logic:equal name="mixingForm" property="use_own_random_seed" value="false">
            <html:text property="rng_seed" size="5" disabled="true" />
        </logic:equal>
    </span>
</div>
<div id="real_particle_shape_set">
    <span id="real_shapes">
        <html:hidden property="real_shapes" />
        <logic:equal name="mixingForm" property="real_shapes" value="true">
            <input type="checkbox" name="real_shapes_checkbox" CHECKED onclick="useRealParticleShapes(this);"/> Use real particle shapes with shape set:
        </logic:equal>
        <logic:equal name="mixingForm" property="real_shapes" value="false">
            <input type="checkbox" name="real_shapes_checkbox" onclick="useRealParticleShapes(this);"/> Use real particle shapes with shape set:
        </logic:equal>
    </span>
    <span id="shape_set">
        <logic:equal name="mixingForm" property="real_shapes" value="true">
            <html:select property="shape_set" onchange="onChangeParticleShape(this);">
                <span id="particle_shape_sets"><html:options name="cement_database" property="particle_shape_sets" /></span>
            </html:select>
        </logic:equal>
        <logic:equal name="mixingForm" property="real_shapes" value="false">
            <html:select property="shape_set" onchange="onChangeParticleShape(this);" disabled="true">
                <span id="particle_shape_sets"><html:options name="cement_database" property="particle_shape_sets" /></span>
            </html:select>
        </logic:equal>
    </span>
</div>
<div id="flocculation">
    <span id="use_flocculation">
        <html:hidden property="use_flocculation" />
        <logic:equal name="mixingForm" property="use_flocculation" value="true">
            <input type="checkbox" name="use_flocculation_checkbox" CHECKED onclick="useFlocculation(this);" /> Flocculation. Degree of flocculation:
        </logic:equal>
        <logic:equal name="mixingForm" property="use_flocculation" value="false">
            <input type="checkbox" name="use_flocculation_checkbox" onclick="useFlocculation(this);" /> Flocculation. Degree of flocculation:
        </logic:equal>
    </span>
    <span id="flocdegree">
        <logic:equal name="mixingForm" property="use_flocculation" value="true">
            <html:text property="flocdegree" size="5" /> (0.0 to 1.0)
        </logic:equal>
        <logic:equal name="mixingForm" property="use_flocculation" value="false">
            <html:text property="flocdegree" size="5" disabled="true" /> (0.0 to 1.0)
        </logic:equal>
    </span>
</div>
<div id="dispersion">
    <span id="use_dispersion_distance">
        <html:hidden property="use_dispersion_distance" />
        <logic:equal name="mixingForm" property="use_dispersion_distance" value="true">
            <input type="checkbox" name="use_dispersion_distance_checkbox" CHECKED onclick="useDispersionDistance(this);" /> Dispersion distance
        </logic:equal>
        <logic:equal name="mixingForm" property="use_dispersion_distance" value="false">
            <input type="checkbox" name="use_dispersion_distance_checkbox" onclick="useDispersionDistance(this);" /> Dispersion distance
        </logic:equal>
    </span>
    <span id="dispersion_distance">
        <logic:equal name="mixingForm" property="use_dispersion_distance" value="true">
            <html:select property="dispersion_distance" onchange="onChangeDispersionDistance(this);">
                <option>0</option>
                <option>1</option>
                <option>2</option>
            </html:select>
        </logic:equal>
        <logic:equal name="mixingForm" property="use_dispersion_distance" value="false">
            <html:select property="dispersion_distance" disabled="true" onchange="onChangeDispersionDistance(this);">
                <option>0</option>
                <option>1</option>
                <option>2</option>
            </html:select>
        </logic:equal>
    </span>
</div>
        <br>
<table style="width:33%; float:left; border-collapse:collapse;">
    <thead>
        <tr>
            <th colspan="3" align="left">
				System size for the binder:
            </th>
        </tr>
    </thead>
    <tr>
        <td>x dimension</td>
        <td>
            <span id="binder_x_dim">
                <html:text property="binder_x_dim" size="4" onchange="onChangeBinderSystemSize(this);" />
            </span>
        </td>
        <td>microns</td>
    </tr>
    <tr>
        <td>y dimension</td>
        <td>
            <span id="binder_y_dim">
                <html:text property="binder_y_dim" size="4" onchange="onChangeBinderSystemSize(this);" />
            </span>
        </td>
        <td>microns</td>
    </tr>
    <tr>
        <td>z dimension</td>
        <td>
            <span id="binder_z_dim">
                <html:text property="binder_z_dim" size="4" onchange="onChangeBinderSystemSize(this);" />
            </span>
        </td>
        <td>microns</td>
    </tr>
    <tr class="hidden">
        <td>
			Resolution
        </td>
        <td>
            <span id="binder_resolution">
                <html:select property="binder_resolution">
                    <option>1.0</option>
                    <option>0.75</option>
                    <option>0.50</option>
                    <option>0.25</option>
                </html:select>
				microns/pixel
            </span>
        </td>
        <td>microns/pixel</td>
    </tr>
</table>

<logic:equal name="mixingForm" property="use_visualize_concrete" value="true">
    <table id="concrete_system_size_table" style="width:40%; float: right; border-collapse: collapse;">
    </logic:equal>
    <logic:equal name="mixingForm" property="use_visualize_concrete" value="false">
        <table id="concrete_system_size_table" class="hidden" style="width:40%; float: right; border-collapse: collapse;">
        </logic:equal>
        <thead>
            <tr>
                <th colspan="3" align="left">System size for the concrete:</th>
            </tr>
        </thead>
        <tr>
            <td>x dimension</td>
            <td>
                <span id="concrete_x_dim">
                    <html:text property="concrete_x_dim" size="4" onchange="onChangeConcreteSystemSize(this);" />
                </span>
            </td>
            <td>millimeters</td>
        </tr>
        <tr>
            <td>y dimension</td>
            <td>
                <span id="concrete_y_dim">
                    <html:text property="concrete_y_dim" size="4" onchange="onChangeConcreteSystemSize(this);" />
                </span>
            </td>
            <td>millimeters</td>
        </tr>
        <tr>
            <td>z dimension</td>
            <td>
                <span id="concrete_z_dim">
                    <html:text property="concrete_z_dim" size="4" onchange="onChangeConcreteSystemSize(this);" />
                </span>
            </td>
            <td>millimeters</td>
        </tr>
        <tr>
            <td>
			Resolution
            </td>
            <td>
                <span id="concrete_resolution">
                    <html:text property="concrete_resolution" size="4" onchange="onChangeConcreteSystemResolution(this);" />
                </span>
            </td>
            <td>millimeters/pixel</td>
        </tr>
        <tr>
            <th colspan="3" align="left">
                <span id="use_visualize_concrete">
                    <html:hidden property="use_visualize_concrete" />
                    <input type="checkbox" name="use_visualize_concrete_checkbox" onclick="useVisualizeConcrete(this);" /> Create the aggregate packing
                </span>
            </th>
        </tr>
    </table>