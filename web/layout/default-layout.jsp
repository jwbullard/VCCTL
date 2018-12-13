<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8" language="java"%>
<%@taglib uri="http://struts.apache.org/tags-html" prefix="html" %>
<%@taglib uri="http://struts.apache.org/tags-tiles" prefix="tiles" %>

<html:html lang="en" xhtml="true">
	<head>
		<html:base/>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
		<meta name="pragma" content="no-cache" />
		<meta name="cache-control" content="no-cache" />
		<meta name="expires" content="0" />
		<title>
			<tiles:getAsString name="title" />
		</title>
		<link rel="stylesheet" href="<%=request.getContextPath()%>/css/default-layout.css" type="text/css"/>
		<link rel="stylesheet" href="<%=request.getContextPath()%>/css/menu.css" type="text/css"/>
		<link rel="stylesheet" href="<%=request.getContextPath()%>/css/operations-files.css" type="text/css"/>
		<script src="<%=request.getContextPath()%>/script/prototype.js" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/menu-tabs.js" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/ajax.js" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/vcctl-functions.js" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/scriptaculous.js?load=slider,effects" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/checkings.js" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/chart.js" type="text/javascript"></script>
		<script src="<%=request.getContextPath()%>/script/Tooltip.js" type="text/javascript"></script>
	</head>
	<body>
		<tiles:insert attribute="header" />
		<!-- Here comes the tab menu -->
		<tiles:insert attribute="menu" />
		<div id="main">
			<div id="top-border">
				<div id="top-left-border"></div> 
				<div id="top-right-border"></div>
			</div>
			<!-- Here comes the submenu, hidden by default -->
			<tiles:insert attribute="sub-menu" />
			<div id="content-left">
				<div id="content-right">
					<!-- Here comes the content -->
					<div id="preloader" style="display: none">
						<div id="preloadIMG">
						</div>
					</div>
					<div id="content">
						<tiles:insert attribute="content" />
					</div>
				</div>
			</div>
			<div id="bottom-border">
				<div id="bottom-left-border"></div> 
				<div id="bottom-right-border"></div>
			</div>
		</div>
		<tiles:insert attribute="footer" />
	</body>
</html:html>