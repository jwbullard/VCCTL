/*
 * ServletChartMaker.java
 *
 * Created on July 24, 2007, 12:40 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.measurements;

import java.io.IOException;
import java.util.regex.*;
import javax.servlet.http.HttpServletRequest;
import org.jfree.chart.ChartRenderingInfo;
import org.jfree.chart.ChartUtilities;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.entity.StandardEntityCollection;
import org.jfree.chart.servlet.ServletUtilities;
import org.jfree.data.Range;

/**
 *
 * @author mscialom
 */
public class ServletChartMaker {
    
    public static ServletChart createSmallPNGChart(JFreeChart chart, HttpServletRequest request) throws IOException {
        return createPNGChart(chart, 512, 384, request);
    }
    
    public static ServletChart createBigPNGChart(JFreeChart chart, HttpServletRequest request) throws IOException {
        return createPNGChart(chart, 1024, 768, request);
    }
    
    public static ServletChart createPNGChart(JFreeChart chart, int length, int height, HttpServletRequest request) throws IOException {
        
        ChartRenderingInfo info = new ChartRenderingInfo(new StandardEntityCollection());
        String filename = ServletUtilities.saveChartAsPNG(chart, length, height, info, request.getSession());
        
        return createServletChart(chart, request, info, filename);
    }
    
    public static ServletChart createSmallJPEGChart(JFreeChart chart, HttpServletRequest request) throws IOException {
        return createJPEGChart(chart, 512, 384, request);
    }
    
    public static ServletChart createBigJPEGChart(JFreeChart chart, HttpServletRequest request) throws IOException {
        return createJPEGChart(chart,1024, 768, request);
    }
    
    public static ServletChart createJPEGChart(JFreeChart chart, int length, int height, HttpServletRequest request) throws IOException {
        
        ChartRenderingInfo info = new ChartRenderingInfo(new StandardEntityCollection());
        String filename = ServletUtilities.saveChartAsJPEG(chart, length, height, info, request.getSession());
        
        return createServletChart(chart, request, info, filename);
    }
    
    public static ServletChart createServletChart(JFreeChart chart, HttpServletRequest request, ChartRenderingInfo info, String filename) {
        String map = ChartUtilities.getImageMap(filename,info);
        
        /**
         * Extract useful  values from image map and chart axis ranges
         * Those values are used to allow the user to zoom on the image from the jsp page
         * See the javascript scripts associated with the measure-hydrated-mix.jsp page
         **/
        String[] lines = map.split("\n");
        String coordsString;
        String[] coords;
        int xMin = Integer.MAX_VALUE, xMax = Integer.MIN_VALUE, yMin = Integer.MAX_VALUE, yMax = Integer.MIN_VALUE, x, y;
        Pattern pattern = Pattern.compile("coords=\"(([0-9]+,[0-9]+)+)\"");
        Matcher matcher;
        for (int i = 0; i < lines.length; i++) {
            matcher = pattern.matcher(lines[i].trim());
            if (matcher.find()) {
                coordsString = matcher.group(1);
                coords = coordsString.split(",");
                for (int j = 0; j < coords.length; j += 2) {
                    x = Integer.parseInt(coords[j]);
                    if (x < xMin)
                        xMin = x;
                    if (x > xMax)
                        xMax = x;
                    y = Integer.parseInt(coords[j+1]);
                    if (y < yMin)
                        yMin = y;
                    if (y > yMax)
                        yMax = y;
                }
            }
        }
        xMin = xMin + 3;
        xMax = xMax - 3;
        yMin = yMin + 3;
        yMax = yMax - 3;
        
        Range xDataRange = chart.getXYPlot().getDataRange(chart.getXYPlot().getDomainAxis());
        Range xDisplayedRange = chart.getXYPlot().getDomainAxis().getRange();
        Range yDataRange = chart.getXYPlot().getDataRange(chart.getXYPlot().getRangeAxis());
        Range yDisplayedRange = chart.getXYPlot().getRangeAxis().getRange();
        
        double xMinValue = xDataRange.getLowerBound();
        if (xDisplayedRange.getLowerBound() > xMinValue)
            xMinValue = xDisplayedRange.getLowerBound();
        
        double xMaxValue = xDataRange.getUpperBound();
        if (xDisplayedRange.getUpperBound() < xMaxValue)
            xMaxValue = xDisplayedRange.getUpperBound();
        
        double yMinValue = yDataRange.getLowerBound();
        if (yDisplayedRange.getLowerBound() > yMinValue)
            yMinValue = yDisplayedRange.getLowerBound();
        
        double yMaxValue = yDataRange.getUpperBound();
        if (yDisplayedRange.getUpperBound() < yMaxValue)
            yMaxValue = yDisplayedRange.getUpperBound();
        
        String src = request.getContextPath()+"/servlet/DisplayChart?filename=" + filename;
        String useMap = "#" + filename;
        
        return new ServletChart(map, src, useMap,
                Integer.toString(xMin), Integer.toString(xMax), Integer.toString(yMin), Integer.toString(yMax),
                Double.toString(xMinValue), Double.toString(xMaxValue),
                Double.toString(yMinValue), Double.toString(yMaxValue));
    }
}
