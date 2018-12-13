<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java"%>
<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>

<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
		<meta name="pragma" content="no-cache" />
		<meta name="cache-control" content="no-cache" />
		<meta name="expires" content="0" />
		<title>Hydration Movie Viewer</title>
		<link rel="stylesheet" href="<%=request.getContextPath()%>/css/operations-files.css" type="text/css"/>
	</head>
	<body>
		<html:form action="/my-files/viewHydrationMovie.do">
			<bean:define name="viewHydrationMovieForm" id="movieName" property="movieName" />
                        <bean:define name="viewHydrationMovieForm" id="optype" property="optype" />
			Image Name: <bean:write name="viewHydrationMovieForm" property="movieName" />
                        <br></br>
			Magnification: <html:text property="magnification" size="4" />X
                        <br></br>
                        Backscattered Electron Contrast:
                        <html:select property="bse">
                            <html:option value="yes" />
                            <html:option value="no" />
                        </html:select>
                        <br></br>
                        Speed: <html:text property="framespeed" size="4" /> frames/s
                        <br></br>
			<html:submit>Get movie</html:submit>
                        <br></br>
			<div id="movie-image" >
				<img src="/vcctl/image/<%=movieName%>" alt="Should be an animated gif here!" />
			</div>
			<fieldset class="legend">
				<legend>Legend</legend>
                               <% if (optype.equals("Microstructure")) { %>
					<div class="legend-item">
						<html:img page="/image/c3s.gif" />
						<div class="legend-title">C<sub>3</sub>S</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/c2s.gif" />
						<div class="legend-title">C<sub>2</sub>S</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/c3a.gif" />
						<div class="legend-title">C<sub>3</sub>A</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/c4af.gif" />
						<div class="legend-title">C<sub>4</sub>AF</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/k2so4.gif" />
						<div class="legend-title">K<sub>2</sub>SO<sub>4</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/na2so4.gif" />
						<div class="legend-title">Na<sub>2</sub>SO<sub>4</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/gypsum.gif" />
						<div class="legend-title">Gypsum</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/hemihyd.gif" />
						<div class="legend-title">Hemihydrate</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/anhydrite.gif" />
						<div class="legend-title">Anhydrite</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/inert.gif" />
						<div class="legend-title">Inert</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/caco3.gif" />
						<div class="legend-title">CaCO<sub>3</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/freelime.gif" />
						<div class="legend-title">Free Lime</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/sfume.gif" />
						<div class="legend-title">Silica</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/inertagg.gif" />
						<div class="legend-title">Aggregate</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/cas2.gif" />
						<div class="legend-title">CAS<sub>2</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/slag.gif" />
						<div class="legend-title">Slag</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/asg.gif" />
						<div class="legend-title">ASG</div>
					</div>
                                <% } else if (optype.equals("Aggregate")) { %>
                                        <div class="legend-item">
						<html:img page="/image/c3a.gif" />
						<div class="legend-title">Binder</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/coarseagg01.gif" />
						<div class="legend-title">Coarse 1</div>
					</div>
                                        <div class="legend-item">
						<html:img page="/image/coarseagg02.gif" />
						<div class="legend-title">Coarse 2</div>
					</div>
                                        <div class="legend-item">
						<html:img page="/image/fineagg01.gif" />
						<div class="legend-title">Fine 1</div>
					</div>
                                        <div class="legend-item">
						<html:img page="/image/fineagg02.gif" />
						<div class="legend-title">Fine 2</div>
					</div>
                                        <div class="legend-item">
						<html:img page="/image/c2s.gif" />
						<div class="legend-title">ITZ</div>
					</div>
                                <% } else { %>
                                	<div class="legend-item">
						<html:img page="/image/c3s.gif" />
						<div class="legend-title">C<sub>3</sub>S</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/c2s.gif" />
						<div class="legend-title">C<sub>2</sub>S</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/c3a.gif" />
						<div class="legend-title">C<sub>3</sub>A</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/c4af.gif" />
						<div class="legend-title">C<sub>4</sub>AF</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/k2so4.gif" />
						<div class="legend-title">K<sub>2</sub>SO<sub>4</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/na2so4.gif" />
						<div class="legend-title">Na<sub>2</sub>SO<sub>4</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/gypsum.gif" />
						<div class="legend-title">Gypsum</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/hemihyd.gif" />
						<div class="legend-title">Hemihydrate</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/anhydrite.gif" />
						<div class="legend-title">Anhydrite</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/inert.gif" />
						<div class="legend-title">Inert</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/caco3.gif" />
						<div class="legend-title">CaCO<sub>3</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/freelime.gif" />
						<div class="legend-title">Free Lime</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/sfume.gif" />
						<div class="legend-title">Silica</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/inertagg.gif" />
						<div class="legend-title">Aggregate</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/cas2.gif" />
						<div class="legend-title">CAS<sub>2</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/slag.gif" />
						<div class="legend-title">Slag</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/asg.gif" />
						<div class="legend-title">ASG</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/ch.gif" />
						<div class="legend-title">CH</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/csh.gif" />
						<div class="legend-title">C-S-H</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/slagcsh.gif" />
						<div class="legend-title">Slag C-S-H</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/pozzcsh.gif" />
						<div class="legend-title">Pozz C-S-H</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/ettr.gif" />
						<div class="legend-title">Ettringite</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/afm.gif" />
						<div class="legend-title">AFm</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/strat.gif" />
						<div class="legend-title">Stratlingite</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/cacl2.gif" />
						<div class="legend-title">CaCl<sub>2</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/friedel.gif" />
						<div class="legend-title">Friedel Salt</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/fh3.gif" />
						<div class="legend-title">FH<sub>3</sub></div>
					</div>
					<div class="legend-item">
						<html:img page="/image/brucite.gif" />
						<div class="legend-title">Brucite</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/ms.gif" />
						<div class="legend-title">MS</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/default.gif" />
						<div class="legend-title">Other Solid</div>
					</div>
					<div class="legend-item">
						<html:img page="/image/emptyp.gif" />
						<div class="legend-title">Empty Porosity</div>
					</div>
                              <% } %>
			</fieldset>
		</html:form>
	</body>
</html>
