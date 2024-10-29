<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/2000/REC-xhtml1-20000126/DTD/xhtml1-transitional.dtd">

<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java" %>

<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-bean" prefix="bean" %>
<%@taglib uri="http://struts.apache.org/tags-logic" prefix="logic" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>

<html:html>
	<head>
		<html:base/>
		<title>Measurements</title>
		<script src="<%=request.getContextPath()%>/script/chart.js" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/prototype.js" type="text/javascript"></script>
	</head>

	<body>
		<div id="preloader" style="display: none">
			<div id="preloadIMG" style="width: 32px; height: 32px; position: relative; left: 384px; top: 32px; background-image: url(../images/ajax-loader.gif);">
			</div>
		</div>
		<div id="content">
			<html:form action="/measurements/measureHydratedMix.do">
				<div id="result_graph" class="chart to-reload">
					<logic:present name="bigChart">
						<input type="hidden" value="${bigChart.XMin}" name="xMin"/>
						<input type="hidden" value="${bigChart.XMax}" name="xMax"/>
						<input type="hidden" value="${bigChart.YMin}" name="yMin"/>
						<input type="hidden" value="${bigChart.YMax}" name="yMax"/>
						<input tYpe="hidden" value="${bigChart.XMinValue}" name="xMinValue"/>
						<input type="hidden" value="${bigChart.XMaxValue}" name="xMaxValue"/>
						<input type="hidden" value="${bigChart.YMinValue}" name="yMinValue"/>
						<input type="hidden" value="${bigChart.YMaxValue}" name="yMaxValue"/>
						<div id="selection-rect" style="position: absolute; cursor: crosshair; border-right: 1px solid #000; border-left: 1px solid #000;" onmouseup="onMouseUpOnBigChart(event,this);" onmousemove="onMouseMoveOnBigChart(event,this);">
						</div>
						<div id="result_big_graph_img" style="cursor: crosshair; width: 1024px; height: 768px; background: url(${bigChart.src}) no-repeat right;" onmousedown="onMouseDownOnChart(event,this);" onmouseup="onMouseUpOnBigChart(event,this);" onmousemove="onMouseMoveOnBigChart(event,this);" ondblclick="onDoubleClickOnBigChart(event,this);">
						</div>
					</logic:present>
				</div>
			</html:form>
		</div>
	</body>
</html:html>