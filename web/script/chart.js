var CHART_MOUSE_ZOOMING_SAFETY_COEFFICIENT = 0.01;

var mouseDown;
var startX;
var endX;
var xMin;
var xMax;
var yMin;
var yMax;

function onMouseDownOnChart(e) {
	var theForm = document.forms[0];
	mouseDown = true;
	$('selection-rect').show();
	var coords = getMouseCoordinates(e);
	startX = coords.x;
	xMin = parseInt(theForm.xMin.value);
	xMax = parseInt(theForm.xMax.value);
	yMin = parseInt(theForm.yMin.value);
	yMax = parseInt(theForm.yMax.value);
}

function onMouseUpOnSmallChart(e) {
	onMouseUpOnChart(e, $('result_graph_img'));
}

function onMouseUpOnBigChart(e) {
	onMouseUpOnChart(e, $('result_big_graph_img'));
}

function onMouseUpOnChart(e, element) {
	var theForm = document.forms[0];
	mouseDown = false;
	var coords = getMouseCoordinates(e);
	endX = coords.x;
	if (endX < startX) {
		var temp = endX;
		endX = startX;
		startX = temp;
	}
	$('selection-rect').hide();

	/* First check if the user didn't mean to double click */
	if ((endX > (startX * (1 + CHART_MOUSE_ZOOMING_SAFETY_COEFFICIENT)))) {
		var xMinValue = parseInt(theForm.xMinValue.value);
		var xMaxValue = parseInt(theForm.xMaxValue.value);
		var ratio = (xMaxValue - xMinValue) / (xMax - xMin);
		var offSet = Position.cumulativeOffset(element);
		var graphLeft = offSet[0];
		var lowerBound = ((startX - graphLeft - xMin) * ratio) + xMinValue;
		var upperBound = ((endX - graphLeft - xMin) * ratio) + xMinValue;
		$('preloader').show();
		$('content').hide();
		if (element.id == "result_big_graph_img") {
			action = "change_big_graph_boundaries";
		} else if (element.id == "result_graph_img") {
			action = "change_graph_boundaries";
		}
		var url = '/vcctl/measurements/measureHydratedMix.do?action=' + action +'&lowerBound=' + lowerBound + '&upperBound=' + upperBound;
		new Ajax.Updater('content', url, {
			onComplete:function() {
				$('preloader').hide();
				$('content').show();
				}, evalScripts:true
			});
		} else {
			if (element.id == "result_big_graph_img") {
				onDoubleClickOnBigChart(e,element);
			} else if (element.id == "result_graph_img") {
				onDoubleClickOnSmallChart(e,element);
			}
		}
}

function onMouseMoveOnSmallChart(e) {
	onMouseMoveOnChart(e, $('result_graph_img'));
}

function onMouseMoveOnBigChart(e) {
	onMouseMoveOnChart(e, $('result_big_graph_img'));
}

function onMouseMoveOnChart(e, element) {
	if (mouseDown) {
		var coords = getMouseCoordinates(e);
		endX = coords.x;
		var offSet = Position.cumulativeOffset(element);
		var graphLeft = offSet[0];
		var graphTop = offSet[1];
		if (endX < startX) {
			var temp = endX;
			endX = startX;
			startX = temp;
		}
		if (startX < (graphLeft + xMin)) {
			startX = graphLeft + xMin;
		}
		if (endX > (graphLeft + xMax)) {
			endX = graphLeft + xMax;
		}
		$('selection-rect').setStyle({
			left: startX + "px",
			width: (endX - startX) + "px",
			top: (graphTop + yMin) + "px",
			height: (yMax - yMin) + "px"
		});
	}
}

function onDoubleClickOnSmallChart(e) {
	onDoubleClickOnChart(e, $('result_graph_img'));
}

function onDoubleClickOnBigChart(e) {
	onDoubleClickOnChart(e, $('result_big_graph_img'));
}

function onDoubleClickOnChart(e, element) {
	$('preloader').show();
	$('content').hide();
	if (element.id == "result_big_graph_img") {
		action = "change_big_graph_boundaries";
	} else if (element.id == "result_graph_img") {
		action = "change_graph_boundaries";
	}
	var url = '/vcctl/measurements/measureHydratedMix.do?action=' + action +'&lowerBound=0.0&upperBound=0.0'; // allow to redraw the graph to its full size
	new Ajax.Updater('content', url, {
		onComplete:function() {
			$('preloader').hide();
			$('content').show();
		}, evalScripts:true
	});
}

function getMouseCoordinates(e) {
	var coords = {};
	coords.x = 0;
	coords.y = 0;
	if (!e) var e = window.event;
	if (e.pageX || e.pageY) 	{
		coords.x = e.pageX;
		coords.y = e.pageY;
	}
	else if (e.clientX || e.clientY) 	{
		coords.x = e.clientX + document.body.scrollLeft
		+ document.documentElement.scrollLeft;
		coords.x = e.clientY + document.body.scrollTop
		+ document.documentElement.scrollTop;
	}
	// x and y contain the mouse ition relative to the document
	// Do something with this information
	return coords;
}