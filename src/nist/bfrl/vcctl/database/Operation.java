/*
 * Operation.java
 *
 * Created on April 29, 2005, 1:46 PM
 */

package nist.bfrl.vcctl.database;

import java.io.*;
import java.io.File;
import java.sql.Timestamp;
import java.text.Format;
import java.text.SimpleDateFormat;
import java.util.HashMap;
import java.util.Map;
import java.util.ArrayList;
import nist.bfrl.vcctl.image.ImageSlice;
import nist.bfrl.vcctl.image.MicrostructureMovie;
import nist.bfrl.vcctl.image.HydrationMovie;
import nist.bfrl.vcctl.image.BarChart;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.FileTypes;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.util.UserDirectory;

/**
 *
 * @author tahall
 */
public class Operation {
    
    /**
     * Holds value of property name.
     */
    private String name;
    
    /**
     * Holds value of property username.
     */
    private String username;
    
    /**
     * Holds value of property type.
     */
    private String type;
    
    /**
     * Holds value of property state.
     */
    private byte[] state;
    
    /**
     * Holds value of property queue.
     */
    private Timestamp queue;
    
    /**
     * Holds value of property start.
     */
    private Timestamp start;
    
    /**
     * Holds value of property finish.
     */
    private Timestamp finish;
    
    /**
     * Holds value of property status.
     */
    private String status;
    
    /**
     * Holds value of property depends_on_operation_name.
     */
    private String depends_on_operation_name;
    
    
    /** Creates a new instance of Operation */
    public Operation(String name, String userName, String type) {
        this.name = name;
        this.username = userName;
        this.type = type;
        this.queue = null;
        this.start = null;
        this.finish = null;
        this.status = Constants.OPERATION_QUEUED_STATUS;
        this.depends_on_operation_name = "";
        this.depends_on_operation_username = "";
        this.setNotes("");
        this.viewOperation = false;
        
        this.state = null;
    }
    
    /**
     * Getter for property name.
     * @return Value of property name.
     */
    public String getName() {
        
        return this.name;
    }
    
    /**
     * Setter for property name.
     * @param name New value of property name.
     */
    public void setName(String name) {
        
        this.name = name;
        
    }
    
    /**
     * Getter for property username.
     * @return Value of property username.
     */
    public String getUsername() {
        
        return this.username;
    }
    
    /**
     * Setter for property username.
     * @param username New value of property username.
     */
    public void setUsername(String username) {
        
        this.username = username;
    }
    
    /**
     * Getter for property type.
     * @return Value of property type.
     */
    public String getType() {
        
        return this.type;
    }
    
    /**
     * Setter for property type.
     * @param type New value of property type.
     */
    public void setType(String type) {
        
        this.type = type;
    }
    
    /**
     * Getter for property state.
     * @return Value of property state.
     */
    public byte[] getState() {
        
        return this.state;
    }
    
    /**
     * Setter for property state.
     * @param data New value of property state.
     */
    public void setState(byte[] data) {
        
        this.state = data;
    }
    
    /**
     * Getter for property request.
     * @return Value of property request.
     */
    public Timestamp getQueue()  {
        
        return this.queue;
    }
    
    /**
     * Setter for property request.
     * @param request New value of property request.
     */
    public void setQueue(Timestamp queue)  {
        
        this.queue = queue;
    }
    
    /**
     * Getter for property start.
     * @return Value of property start.
     */
    public Timestamp getStart() {
        
        return this.start;
    }
    
    /**
     * Setter for property start.
     * @param start New value of property start.
     */
    public void setStart(Timestamp start) {
        
        this.start = start;
    }
    
    /**
     * Getter for property finish.
     * @return Value of property finish.
     */
    public Timestamp getFinish() {
        
        return this.finish;
    }
    
    /**
     * Setter for property finish.
     * @param finish New value of property finish.
     */
    public void setFinish(Timestamp finish) {
        
        this.finish = finish;
    }
    
    /**
     * Getter for property status.
     * @return Value of property status.
     */
    public String getStatus() {
        
        return this.status;
    }
    
    /**
     * Setter for property status.
     * @param status New value of property status.
     */
    public void setStatus(String status) {
        
        this.status = status;
    }
    
    /**
     * Getter for property depends_on_operation_name.
     * @return Value of property depends_on_operation_name.
     */
    public String getDepends_on_operation_name() {
        
        return this.depends_on_operation_name;
    }
    
    /**
     * Setter for property depends_on_operation_name.
     * @param depends_on_operation_name New value of property depends_on_operation_name.
     */
    public void setDepends_on_operation_name(String depends_on_operation_name) {
        
        this.depends_on_operation_name = depends_on_operation_name;
    }
    
    /**
     * Holds value of property notes.
     */
    private String notes;
    
    /**
     * Getter for property note.
     * @return Value of property note.
     */
    public String getNotes() {
        return this.notes;
    }
    
    /**
     * Setter for property note.
     * @param note New value of property note.
     */
    public void setNotes(String notes) {
        this.notes = notes;
    }
    
    /**
     * Holds value of property depends_on_operation_username.
     */
    private String depends_on_operation_username;
    
    /**
     * Getter for property depends_on_operation_username.
     * @return Value of property depends_on_operation_username.
     */
    public String getDepends_on_operation_username() {
        return this.depends_on_operation_username;
    }
    
    /**
     * Setter for property depends_on_operation_username.
     * @param depends_on_operation_username New value of property depends_on_operation_username.
     */
    public void setDepends_on_operation_username(String depends_on_operation_username) {
        this.depends_on_operation_username = depends_on_operation_username;
    }
    
    /**
     * Getter for property formattedStartTime.
     * @return Value of property formattedStartTime.
     */
    public String getFormattedStartTime() {
        Format formatter = new SimpleDateFormat("d MMM yyyy HH:mm:ss");
        return formatter.format(this.start);
    }
    
    /**
     * Getter for property formattedFinishTime.
     * @return Value of property formattedFinishTime.
     */
    public String getFormattedFinishTime() {
        Format formatter = new SimpleDateFormat("d MMM yyyy HH:mm:ss");
        return formatter.format(this.finish);
    }
    
    /**
     * Holds value of property formattedQueuedTime.
     */
    // private String formattedQueuedTime;
    
    /**
     * Getter for property formattedQueuedTime.
     * @return Value of property formattedQueuedTime.
     */
    public String getFormattedQueuedTime() {
        Format formatter = new SimpleDateFormat("d MMM yyyy HH:mm:ss");
        return formatter.format(this.queue);
    }
    
    public abstract class OperationFile {
        
        public OperationFile(String name, String type) {
            this.name = name;
            this.type = type;
            this.viewContent = false;
        }
        
        /**
         * Holds value of property name.
         */
        protected String name;
        
        /**
         * Getter for property name.
         * @return Value of property name.
         */
        public String getName() {
            return this.name;
        }
        
        /**
         * Setter for property name.
         * @param name New value of property name.
         */
        public void setName(String name) {
            this.name = name;
        }
        
        /**
         * Getter for property description.
         * @return Value of property description.
         */
        public String getDescription() {
            return FileTypes.description(Operation.this.name, this.name);
        }
        
        /**
         * Holds value of property viewContent.
         */
        protected boolean viewContent;
        
        /**
         * Getter for property viewContent.
         * @return Value of property viewContent.
         */
        public boolean getViewContent() {
            return this.viewContent;
        }
        
        /**
         * Setter for property viewContent.
         * @param viewContent New value of property viewContent.
         */
        public void setViewContent(boolean viewContent) {
            this.viewContent = viewContent;
        }
        
        /**
         * Indexed getter for property linkParameters.
         * @param index Index of the property.
         * @return Value of the property at <CODE>index</CODE>.
         */
        public Map<String,String> getLinkParameters() {
            Map<String,String> params = new HashMap();
            params.put("operation",Operation.this.name);
            params.put("file",this.name);
            return params;
        }
        
        /**
         * Holds value of property type.
         */
        protected String type;
        
        /**
         * Getter for property type.
         * @return Value of property type.
         */
        public String getType() {
            return this.type;
        }
        
        /**
         * Setter for property type.
         * @param type New value of property type.
         */
        public void setType(String type) {
            this.type = type;
        }
    }
    
    public final class OperationTextFile extends OperationFile {
        public OperationTextFile(String fileName) {
            super(fileName,"text");
        }
        
        /**
         * Getter for property content.
         * @return Value of property content.
         */
        public String getContent() {
            byte[] fileBytes;
            if (name.startsWith("p" + Operation.this.name)) {
                String pifText = "Cannot view particle image files";
                fileBytes = pifText.getBytes();
            } else {
                fileBytes  = ServerFile.readUserOpBinaryFile(Operation.this.username, Operation.this.name, name);
            }
            String result = new String(fileBytes);
            return result;
        }
        
        /**
         * Getter for property formattedContent.
         * @return Value of property formattedContent.
         */
        public String getFormattedContent() {
            return this.getContent().replaceAll("([\t ])?\n$","").replaceAll("\n","<br/>");
        }
    }
    
    public final class OperationImageFile extends OperationFile {
        public OperationImageFile(String fileName) {
            super(fileName,"image");
            this.magnification = 1;
            this.plane = "yz";
            this.sliceNumber = 50;
            this.viewdepth = 0;
            this.bse = 0;
        }
        
        /**
         * Holds value of property plane.
         */
        private String plane;
        
        /**
         * Getter for property plane.
         * @return Value of property plane.
         */
        public String getPlane() {
            return this.plane;
        }
        
        /**
         * Setter for property plane.
         * @param plane New value of property plane.
         */
        public void setPlane(String plane) {
            this.plane = plane;
        }
        
        /**
         * Holds value of property sliceNumber.
         */
        private int sliceNumber;
        
        /**
         * Getter for property slice.
         * @return Value of property slice.
         */
        public int getSliceNumber() {
            return this.sliceNumber;
        }
        
        /**
         * Setter for property slice.
         * @param slice New value of property slice.
         */
        public void setSliceNumber(int sliceNumber) {
            this.sliceNumber = sliceNumber;
        }
        
        /**
         * Holds value of property magnification.
         */
        private int magnification;
        
        /**
         * Getter for property magnification.
         * @return Value of property magnification.
         */
        public int getMagnification() {
            return this.magnification;
        }
        
        /**
         * Setter for property magnification.
         * @param magnification New value of property magnification.
         */
        public void setMagnification(int magnification) {
            this.magnification = magnification;
        }

        /**
         * Holds value of property viewdepth.
         */
        private int viewdepth;

        /**
         * Getter for property viewdepth.
         * @return Value of property viewdepth.
         */
        public int getViewdepth() {
            return this.viewdepth;
        }

        /**
         * Setter for property viewdepth.
         * @param viewdepth New value of property viewdepth.
         */
        public void setViewdepth(int viewdepth) {
            this.viewdepth = viewdepth;
        }

        /**
         * Holds value of property bse.
         */
        private int bse;

        /**
         * Getter for property bse.
         * @return Value of property bse.
         */
        public int getBse() {
            return this.bse;
        }

        /**
         * Setter for property bse.
         * @param bse New value of property bse.
         */
        public void setBse(int bse) {
            this.bse = bse;
        }
        
        /**
         * Holds value of property sliceName.
         */
        private String sliceName;
        
        /**
         * Getter for property sliceName.
         * @return Value of property sliceName.
         */
        public String getSliceName() {
            /**
             * Convert 'plane' from string to number
             * 1:  xy plane
             * 2:  xz plane
             * 3:  yz plane
             */
            int plane_no = 3; // xy-plane is default
            if (plane.equalsIgnoreCase("xz")) {
                plane_no = 2;
            } else if (plane.equalsIgnoreCase("xy")) {
                plane_no = 1;
            }
            
            /**
             * Generate the 2-D image slice
             */
            ImageSlice is = ImageSlice.INSTANCE;
            
            String slicename = is.createSlice(Operation.this.username, Operation.this.name, name, plane_no, sliceNumber, viewdepth, bse, magnification);
            
            return slicename;
        }
        
        /**
         * Setter for property sliceName.
         * @param sliceName New value of property sliceName.
         */
        public void setSliceName(String sliceName) {
            this.sliceName = sliceName;
        }
        
    }
    
    public final class OperationHydrationMovieFile extends OperationFile {
        public OperationHydrationMovieFile(String fileName) {
            super(fileName,"movie");
            this.magnification = 1;
            this.framespeed = 100.0;
            this.bse = 0;
        }

        /**
         * Holds value of property magnification.
         */
        private int magnification;

        /**
         * Getter for property magnification.
         * @return Value of property magnification.
         */
        public int getMagnification() {
            return this.magnification;
        }

        /**
         * Setter for property magnification.
         * @param magnification New value of property magnification.
         */
        public void setMagnification(int magnification) {
            this.magnification = magnification;
        }

        /**
         * Holds value of property bse.
         */
        private int bse;

        /**
         * Getter for property bse.
         * @return Value of property bse.
         */
        public int getBse() {
            return this.bse;
        }

        /**
         * Setter for property bse.
         * @param bse New value of property bse.
         */
        public void setBse(int bse) {
            this.bse = bse;
        }

         /**
         * Holds value of property framespeed.
         */
        private double framespeed;

        /**
         * Getter for property framespeed.
         * @return Value of property framespeed.
         */
        public double getFramespeed() {
            return this.framespeed;
        }

        /**
         * Setter for property framespeed.
         * @param framespeed New value of property framespeed.
         */
        public void setFramespeed(double framespeed) {
            this.framespeed = framespeed;
        }

        /**
         * Holds value of property movieName.
         */
        private String movieName;

        /**
         * Getter for property movieName.
         * @return Value of property movieName.
         */
        public String getMovieName() {
            /**
             * Generate the movie
             */
            String moviename = new String("MovieFile.gif");
            HydrationMovie hm = HydrationMovie.INSTANCE;
            try {
                moviename = hm.createMovie(Operation.this.username, Operation.this.name, name, bse, magnification, framespeed);
            }
            catch (IOException iox) {
                String msg = iox.getMessage();
                System.out.println(msg);
            }
            return moviename;
        }

        /**
         * Setter for property movieName.
         * @param movieName New value of property sliceName.
         */
        public void setMovieName(String movieName) {
            this.movieName = movieName;
        }

    }
    public final class OperationPoredistFile extends OperationFile {
        public OperationPoredistFile(String fileName) {
            super(fileName,"poredist");
        }

        /**
         * Holds value of property poredistName.
         */
        private String poredistName;

        /**
         * Getter for property poredistName.
         * @return Value of property poredistName.
         */
        public String getPoredistName() {
            /**
             * Generate the pore distribution bar chart
             */
            String poredistname = new String("poredist.png");
            BarChart bc = BarChart.INSTANCE;
            try {
                poredistname = bc.createBarChart(Operation.this.username, Operation.this.name, name);
            }
            catch (IOException iox) {
                String msg = iox.getMessage();
                System.out.println(msg);
            }
            return poredistname;
        }

        /**
         * Setter for property poredistName.
         * @param poredistName New value of property poredistName.
         */
        public void setPoredistName(String poredistName) {
            this.poredistName = poredistName;
        }

    }

    OperationFile[] filesList;
    
    /**
     * Getter for property filesList.
     * @return Value of property filesList.
     */
    public OperationFile[] getFilesList() {
        UserDirectory ud = new UserDirectory(this.username);
        String fileNames[] = ud.getOperationFileNames(this.name);
        if (filesList == null || filesList.length <= 0) {
            ArrayList<OperationFile> filesListArrayList = new ArrayList();
            for (int i = 0; i < fileNames.length; i++) {
                boolean isImage = false;
                boolean isHydrationMovie = false;
                boolean isPoredist = false;
                // if (fileNames[i].equalsIgnoreCase(this.name + ".img")) {
                if (fileNames[i].endsWith(".img")) {
                    isImage = true;
                }
                if (fileNames[i].endsWith(".mov")) {
                    isHydrationMovie = true;
                }
                if (this.type.equalsIgnoreCase(Constants.HYDRATION_OPERATION_TYPE)) {
                    /**
                     * This is a hydration run
                     */
                    if (fileNames[i].contains(".img.")) {
                        isImage = true;
                    }
                    if (fileNames[i].endsWith(".poredist")) {
                        isPoredist = true;
                        isImage = false;
                    }
                }

                boolean valid = !fileNames[i].endsWith(".zip");
                if (isImage) {
                    filesListArrayList.add(new OperationImageFile(fileNames[i]));
                } else if (isHydrationMovie) {
                    filesListArrayList.add(new OperationHydrationMovieFile(fileNames[i]));
                } else if (isPoredist) {
                    filesListArrayList.add(new OperationPoredistFile(fileNames[i]));
                } else if (valid) {
                    filesListArrayList.add(new OperationTextFile(fileNames[i]));
                }
            }
            filesList = (OperationFile[]) filesListArrayList.toArray(new OperationFile[filesListArrayList.size()]);
        }
        return filesList;
    }
    
    /**
     * Holds value of property viewOperation.
     */
    private boolean viewOperation;
    
    /**
     * Getter for property viewOperation.
     * @return Value of property viewOperation.
     */
    public boolean isViewOperation() {
        return this.viewOperation;
    }
    
    /**
     * Setter for property viewOperation.
     * @param viewOperation New value of property viewOperation.
     */
    public void setViewOperation(boolean viewOperation) {
        this.viewOperation = viewOperation;
    }
    
    /**
     * Getter for property zipArchiveName.
     * @return Value of property zipArchiveName.
     */
    public String getZipArchiveName() {
        String archiveName = this.name;
        if (this.type.equalsIgnoreCase(Constants.AGGREGATE_OPERATION_TYPE) || archiveName.contains(File.separator)) {
            int index = archiveName.lastIndexOf(File.separator);
            archiveName = archiveName.substring(index + 1);
        }
        archiveName += ".zip";
        return archiveName;
    }

    /**
     * Getter for property escapedName.
     * Due to a common-beans-1.7 bug, we can't have an operation whose name contains a parenthesis and access it by a Map,
     * as it is the case in MyFilesForm.
     * Replace each parenthesis by a char sequence that users will not use (chekings.js forbid some of those special characters)
     * @return Value of property escapedName.
     */
    public String getEscapedName() {
        return this.getName().replace(")",".*$%").replace("(",".*$%");
    }
}
