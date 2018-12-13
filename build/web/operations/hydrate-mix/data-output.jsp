<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>

<jsp:useBean id="cement_database" class="nist.bfrl.vcctl.database.CementDatabaseBean" scope="page" />

<div id="evaluate_percolation_porosity_times" class="to-reload">
	Evaluate percolation of porosity every:
	<html:text property="evaluate_percolation_porosity_times" size="6" /> hours
</div>
<div id="evaluate_percolation_solids_times" class="to-reload">
	Evaluate percolation of total solids every:
	<html:text property="evaluate_percolation_solids_times" size="6" /> hours
</div>
<div id="evaluate_individual_particle_hydration_times" class="to-reload">
	Evaluate individual particle hydration every:
	<html:text property="evaluate_individual_particle_hydration_times" size="6" /> hours
</div>
<div id="output_hydrating_microstructure_times" class="to-reload">
	<html:radio property="output_option" value="specify_times" onclick="onChangeOutputOption(this);"> Output hydrating microstructure every
	</html:radio>
	<logic:equal name="hydrationForm" property="output_option" value="specify_times">
		<html:text property="output_hydrating_microstructure_times" size="6" /> hours
	</logic:equal>
	<logic:notEqual name="hydrationForm" property="output_option" value="specify_times">
		<html:text property="output_hydrating_microstructure_times" size="6" disabled="true" /> hours
	</logic:notEqual>
</div>
<div id="file_with_output_times" class="to-reload">
	<html:radio property="output_option" value="specify_file" onclick="onChangeOutputOption(this)"> Specify file with times for output
	</html:radio>
	<logic:equal name="hydrationForm" property="output_option" value="specify_file">
		<html:select property="file_with_output_times">
			<html:options name="cement_database" property="timing_output_files" />
		</html:select>
	</logic:equal>
	<logic:notEqual name="hydrationForm" property="output_option" value="specify_file">
		<html:select property="file_with_output_times" disabled="true">
			<html:options name="cement_database" property="timing_output_files" />
		</html:select>
	</logic:notEqual>
</div>
<div id="create_movie_frames" class="to-reload">
	<html:checkbox property="create_movie" onclick="createMovie(this);"/>
	Output hydration movie frame every 
	<html:text property="create_movie_frames" disabled="true" size="6" onchange="onChangeMovieFrames(this);" /> hours
</div>