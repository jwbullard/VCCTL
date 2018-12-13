<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<div id="parameter_file" class="to-reload">
	Parameter file:
	<html:select property="parameter_file">
		<html:options name="cement_database" property="parameter_files" />
	</html:select>
</div>
<div id="random_seed">
	<span id="use_own_random_seed" class="to-reload">
		<html:hidden property="use_own_random_seed" />
		<logic:equal name="hydrationForm" property="use_own_random_seed" value="true">
			<input type="checkbox" name="use_own_random_seed_checkbox" CHECKED onclick="useOwnRandomSeed(this);" /> Use my own random number generator seed:
		</logic:equal>
		<logic:equal name="hydrationForm" property="use_own_random_seed" value="false">
			<input type="checkbox" name="use_own_random_seed_checkbox" onclick="useOwnRandomSeed(this);" /> Use my own random number generator seed:
		</logic:equal>
	</span>
	<span id="rng_seed" class="to-reload">
		<logic:equal name="hydrationForm" property="use_own_random_seed" value="true">
			<html:text property="rng_seed" size="5" />
		</logic:equal>
		<logic:equal name="hydrationForm" property="use_own_random_seed" value="false">
			<html:text property="rng_seed" size="5" disabled="true" />
		</logic:equal>
	</span>
</div>