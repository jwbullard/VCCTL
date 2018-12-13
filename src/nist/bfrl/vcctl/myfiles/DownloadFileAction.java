/*
 * DownloadFileAction.java
 *
 * Created on July 1, 2005, 4:14 PM
 */

package nist.bfrl.vcctl.myfiles;

import java.io.*;
import java.net.URI;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nist.bfrl.vcctl.database.User;
import org.apache.struts.action.ActionForm;
import org.apache.struts.action.ActionMapping;
import org.apache.struts.actions.DownloadAction;


import java.util.zip.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.util.*;

/**
 *
 * @author tahall
 */
public class DownloadFileAction extends DownloadAction {
    
    /** Creates a new instance of DownloadFile */
    public DownloadFileAction() {
    }
    
    protected StreamInfo getStreamInfo(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response)
            throws Exception {
        
        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                
                String operationName = request.getParameter("operation");
                String fileName = request.getParameter("file");
                
                UserDirectory userDir = new UserDirectory(userName);
                
                if (operationName != null) {
                    if (fileName == null) {
                    /*
                     * Case of the user wants to download all the operation files zipped up in one zip file
                     **/
                        String zipFileName = operationName;
                        if (zipFileName.contains(File.separator)) {
                            int index = zipFileName.lastIndexOf(File.separator);
                            zipFileName = zipFileName.substring(index + 1);
                        }
                        zipFileName += ".zip";
                        
                        // Create a zip file containing all other files in the directory
                        // Delete any existing zip archive file
                        userDir.deleteZipFiles(operationName);
                        String[] fileNames = userDir.getOperationFileNames(operationName);
                        
                        if (fileNames != null && fileNames.length > 0) {
                            try {
                                byte[] buf = new byte[1024];
                                String filePath = userDir.getOperationFilePath(operationName,zipFileName);
                                ZipOutputStream out = new ZipOutputStream(new FileOutputStream(filePath));
                                for (int i=0; i<fileNames.length; i++) {
                                    String filePath_i = userDir.getOperationFilePath(operationName, fileNames[i]);
                                    FileInputStream in = new FileInputStream(filePath_i);
                                    
                                    // Add ZIP entry to output stream.  Use file name only,
                                    // do not include the server path information
                                    out.putNextEntry(new ZipEntry(fileNames[i]));
                                    
                                    // Transfer bytes from the file to the ZIP file
                                    int len;
                                    while ((len = in.read(buf)) > 0) {
                                        out.write(buf, 0, len);
                                    }
                                    
                                    // Complete the entry
                                    out.closeEntry();
                                    in.close();
                                }
                                
                                out.close();
                            } catch (IOException iox) {
                                iox.printStackTrace();
                            }
                            
                            // Download a file
                            String contentType = "application/x-download";
                            byte[] fileBytes;
                            fileBytes  = ServerFile.readUserOpBinaryFile(userName, operationName, zipFileName);
                            
                            URI uri = new URI(null,null,zipFileName ,null);
                            zipFileName = uri.toString();
                            
                            response.setHeader("Content-Disposition", "attachment; filename=" + zipFileName);
                            return new ByteArrayStreamInfo(contentType, fileBytes);
                        } else {
                            return null;
                        }
                    } else {
                    /*
                     * Case of the user wants to download a file
                     **/
                        String contentType = "application/x-download";
                        byte[] fileBytes;
                        fileBytes  = ServerFile.readUserOpBinaryFile(userName, operationName, fileName);

                        URI uri = new URI(null,null,fileName ,null);
                        fileName = uri.toString();
                        
                        response.setHeader("Content-Disposition", "attachment; filename=" + fileName);
                        return new ByteArrayStreamInfo(contentType, fileBytes);
                    }
                } else {
                    return null;
                }
            } else {
                return null;
            }
        } else {
            return null;
        }
    }
    
    protected class ByteArrayStreamInfo implements StreamInfo {
        
        protected String contentType;
        protected byte[] bytes;
        
        public ByteArrayStreamInfo(String contentType, byte[] bytes) {
            this.contentType = contentType;
            this.bytes = bytes;
        }
        
        public String getContentType() {
            return contentType;
        }
        
        public InputStream getInputStream() throws IOException {
            return new ByteArrayInputStream(bytes);
        }
    }
}
