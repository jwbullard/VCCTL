/*
 * UploadFileHandler.java
 *
 * Created on February 24, 2006, 11:06 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.labmaterials;

import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.*;
import java.sql.SQLException;
import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.Util;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.FileTypes;
import org.apache.struts.upload.FormFile;
/* import org.apache.commons.io.FileUtils; */
import java.util.zip.*;
import java.util.*;

/**
 *
 * @author tahall
 */
public class UploadFileHandler {

    static public CementUploadResult uploadCementZIPFile(FormFile formFile, Cement cement) throws FileNotFoundException, IOException, SQLArgumentException, SQLException {

        String zipFileName = formFile.getFileName();

        /**
         * 1. Check that uploaded file ends with '.zip'
         *
         */
        if (!zipFileName.endsWith(".zip")) {
            return null;
        }
        String name = zipFileName.substring(0, zipFileName.length() - 4);
        // cement.setName(name);
        

        /**
         * 2. Open the zip input stream and read in the entries in the
         *    archive.
         */
        ZipInputStream in = new ZipInputStream(formFile.getInputStream());
        ZipEntry ze = null;
        String column = "";
        byte[] data;

        boolean psdNameAlreadyTaken = false;
        boolean alkaliNameAlreadyTaken = false;
        String psdDataText = null;
        String alkaliDataText = null;

        // Loop through entries (individual files) in zip file
        while ((ze = in.getNextEntry()) != null) {
            name = ze.getName();

            int index = name.lastIndexOf(File.separator);
            name = name.substring(index + 1);

            if (name.length() > 0) {
                if (FileTypes.isValidCementFileName(name)) {

                    column = FileTypes.getCementColumnNameCorrespondingToFileName(name);
                    // Read in the data and set it in the cement object

                    /** bug with the getSize() of the Java API depending on which tool has been used for creating the ZIP file
                     * long length = ze.getSize();
                     * data = new byte[(int)length];
                     * int nbytes = in.read(data,0,(int)length);
                     **/
                    ByteArrayOutputStream stream = new ByteArrayOutputStream();

                    byte[] nbytes = new byte[1024];

                    int len;
                    while ((len = in.read(nbytes)) > 0) {
                        stream.write(nbytes, 0, len);
                    }

                    if (column.equalsIgnoreCase(Constants.ALKALI_CHARACTERISTICS_TYPE)) {
                        if (name.endsWith(".alk")) {
                            name = name.substring(0, name.length() - 4);
                            name = name + " alk";
                        }

                        // Add the ref to the alkali file in the database

                        // CementDatabase.addAlkaliFileName(name);
                        alkaliDataText = stream.toString();
                        if (CementDatabase.isUniqueDBFileName(name)) {
                            // if the ZIP file does not contain an alkali file that have the same name than another one in the database
                            // DefaultNameBuilder.buildDefaultMaterialName(Constants.DB_FILE_TABLE_NAME, name, "");
                            DBFile alkaliCharacteristics = new DBFile(name, Constants.ALKALI_CHARACTERISTICS_TYPE, alkaliDataText);
                            alkaliCharacteristics.saveFromStrings();
                        } else {
                            alkaliNameAlreadyTaken = true;
                        }
                        cement.setAlkaliFile(name);

                    } else if (column.equalsIgnoreCase(Constants.PSD_TYPE)) {
                        if (name.endsWith(".psd")) {
                            name = name.substring(0, name.length() - 4);
                            name = name + " psd";
                        }
                        
                        psdDataText = stream.toString();
                        if (CementDatabase.isUniqueDBFileName(name)) {
                            // if the ZIP file does not contain an psd that have the same name than another one in the database
                            // DefaultNameBuilder.buildDefaultMaterialName(Constants.DB_FILE_TABLE_NAME, name, "");
                            DBFile psd = new DBFile(name, Constants.PSD_TYPE, psdDataText);
                            psd.saveFromStrings();
                        } else {
                            psdNameAlreadyTaken = true;
                        }
                        cement.setPsd(name);
                    } else if (column.equalsIgnoreCase("zip")) {
                        boolean shapeZIPFilePresent = true;
                        /*
                        OutputStream out = new FileOutputStream(name);
                        byte[] buffer = new byte[8192];
                        int leng;
                        while ((leng = in.read(buffer))!= -1) {
                            out.write(buffer,0,leng);
                        }
                        out.close();
                        File zippedfile = new File(name);
                        String pathtoshapes = Vcctl.getParticleShapeSetDirectory();
                        File shapefolder = new File(pathtoshapes);
                        try {
                            unzipFileIntoDirectory(zippedfile, shapefolder);
                        } catch (Exception ex) {
                        ex.printStackTrace();
                        }
                        */
                    } else {
                        data = stream.toByteArray();
                        cement.setColumn(column, data);
                    }
                }
            }
        }
        
        CementUploadResult result = new CementUploadResult(cement, psdNameAlreadyTaken, alkaliNameAlreadyTaken,
                cement.getPsd(), cement.getAlkaliFile(),
                psdDataText, alkaliDataText);

        return result;
    }

    static public AggregateUploadResult uploadAggregateZIPFile(FormFile formFile, Aggregate aggregate) throws FileNotFoundException, IOException, SQLArgumentException, SQLException {

        boolean shapeZIPFilePresent = false;
        String zipFileName = formFile.getFileName();
        String zipname="";
        String shortzipname = "";

        /**
         * 1. Check that uploaded file ends with '.zip'
         *
         */
        if (!zipFileName.endsWith(".zip")) {
            return null;
        }
        String name = zipFileName.substring(0, zipFileName.length() - 4);
        String fullname = "";
        aggregate.setName(name);
        aggregate.setDisplay_name(name);


        /**
         * 2. Open the zip input stream and read in the entries in the
         *    archive.
         */
        ZipInputStream in = new ZipInputStream(formFile.getInputStream());
        ZipEntry ze = null;
        String column = "";
        byte[] data;

        // Loop through entries (individual files) in zip file
        while ((ze = in.getNextEntry()) != null) {
            fullname = ze.getName();

            int index = fullname.lastIndexOf(File.separator);
            name = fullname.substring(index + 1);

            if (name.length() > 0) {
                if (FileTypes.isValidAggregateFileName(name)) {

                    column = FileTypes.getAggregateColumnNameCorrespondingToFileName(name);
                    // Read in the data and set it in the cement object

                    /** bug with the getSize() of the Java API depending on which tool has been used for creating the ZIP file
                     * long length = ze.getSize();
                     * data = new byte[(int)length];
                     * int nbytes = in.read(data,0,(int)length);
                     **/
                    ByteArrayOutputStream stream = new ByteArrayOutputStream();

                    byte[] nbytes = new byte[1024];

                    

                    if (column.equalsIgnoreCase("zip")) {
                        shapeZIPFilePresent = true;
                        // Move the zip file to the aggregate shape directory
                        // and then unzip it.  How to do this?
                        /*
                        zipname = fullname;
                        shortzipname = name;
                        shapeZIPFilePresent = true;
                        String source = zipname;
                        String destination = Vcctl.getAggregateDirectory();
                        if (destination.charAt(destination.length() - 1) != File.separatorChar)
                            destination = destination + File.separator;
                        destination = destination + shortzipname;
                        int len;
                        while ((len = in.read(nbytes)) > 0) {
                            stream.write(nbytes, 0, len);
                        }
                        data = stream.toByteArray();
                        try {
                            FileOutputStream fos = new FileOutputStream(destination);
                            fos.write(data);
                            fos.close();
                        }
                        catch(FileNotFoundException ex) {
                            System.out.println("FileNotFoundException : " + ex);
                        }
                        catch(IOException ioe){
                            System.out.println("IOException : " + ioe);
                        }
                        Util.unzipFile(destination);
                        */

                    } else {
                        int len;
                        while ((len = in.read(nbytes)) > 0) {
                            stream.write(nbytes, 0, len);
                        }
                        data = stream.toByteArray();
                        aggregate.setColumn(column, data);
                    }
                }
            }
        }

        if (shapeZIPFilePresent) {
            AggregateUploadResult result = new AggregateUploadResult(aggregate,shapeZIPFilePresent);
            return result;
        }

        return null;
    }

    static private DBFile uploadDBFile(FormFile formFile, String fileType) throws SQLArgumentException, SQLException, IOException {
        String fileName = formFile.getFileName();

        String name = null;

        String dataText = null;

        int dotIndex = fileName.lastIndexOf('.');

        /**
         * 1. Check that uploaded file ends with '.zip'
         *
         */
        if (fileName.endsWith(".zip")) {

            /**
             * 2. Open the zip input stream and read in the entries in the
             *    archive.
             */
            ZipInputStream in = new ZipInputStream(formFile.getInputStream());
            ZipEntry ze = null;

            // Loop through entries (individual files) in zip file
            while ((ze = in.getNextEntry()) != null) {
                name = ze.getName();

                int index = name.lastIndexOf(File.separator);
                name = name.substring(index + 1);

                if (name.length() > 0) {
                    String column = FileTypes.getCementColumnNameCorrespondingToFileName(name);
                    if (column.equalsIgnoreCase(fileType)) {

                        dotIndex = name.lastIndexOf('.');
                        if (dotIndex > 0) {
                            name = name.substring(0, dotIndex);
                        }

                        // Read in the data and set it in the cement object

                        /** bug with the getSize() of the Java API depending on which tool has been used for creating the ZIP file
                         * long length = ze.getSize();
                         * data = new byte[(int)length];
                         * int nbytes = in.read(data,0,(int)length);
                         **/
                        ByteArrayOutputStream stream = new ByteArrayOutputStream();

                        byte[] nbytes = new byte[1024];

                        int len;
                        while ((len = in.read(nbytes)) > 0) {
                            stream.write(nbytes, 0, len);
                        }
                        dataText = stream.toString();
                    }
                }
            }
        } else if (dotIndex > 0) {
            fileName = fileName.substring(0, dotIndex);
            dataText = fileName.getBytes().toString();
        }
        if (!CementDatabase.isUniqueDBFileName(fileName)) {
            return null;
        }

        DBFile dbFile = new DBFile(name, fileType, dataText);
        dbFile.saveFromStrings();
        return dbFile;
    }
    
    static private DBFile uploadPSD(FormFile formFile) throws SQLArgumentException, SQLException, IOException {
        return uploadDBFile(formFile, Constants.PSD_TYPE);
    }
    
    static private DBFile uploadAlakaliCharacteristics(FormFile formFile) throws SQLArgumentException, SQLException, IOException {
        return uploadDBFile(formFile, Constants.ALKALI_CHARACTERISTICS_TYPE);
    }
    
    static private DBFile uploadSlagCharacterstics(FormFile formFile) throws SQLArgumentException, SQLException, IOException {
        return uploadDBFile(formFile, Constants.SLAG_CHARACTERISTICS_TYPE);
    }
    
    static private DBFile uploadParameterFile(FormFile formFile) throws SQLArgumentException, SQLException, IOException {
        return uploadDBFile(formFile, Constants.PARAMETER_FILE_TYPE);
    }
    
    static private DBFile uploadCalorimetryFile(FormFile formFile) throws SQLArgumentException, SQLException, IOException {
        return uploadDBFile(formFile, Constants.CALORIMETRY_FILE_TYPE);
    }
    
    static private DBFile uploadChemicalShrinkage(FormFile formFile) throws SQLArgumentException, SQLException, IOException {
        return uploadDBFile(formFile, Constants.CHEMICAL_SHRINKAGE_FILE_TYPE);
    }
    
    static private DBFile uploadTimingOutputFile(FormFile formFile) throws SQLArgumentException, SQLException, IOException {
        return uploadDBFile(formFile, Constants.TIMING_OUTPUT_FILE_TYPE);
    }

    /**
     * @param zipFile
     * @param jiniHomeParentDir
     */
    /*
    static public void unzipFileIntoDirectory(File archive, File destinationDir) throws Exception {

      BufferedOutputStream dest = null;
      FileInputStream fis = new FileInputStream(archive);
      ZipInputStream zis = new ZipInputStream(new BufferedInputStream(fis));
      ZipEntry entry;
      
      while ((entry = zis.getNextEntry()) != null) {
          File destFile = new File(destinationDir, entry.getName());

            if (entry.isDirectory()) {
                destFile.mkdirs();
                continue;
            } else {
                int count;
                byte data[] = new byte[1024];

                destFile.getParentFile().mkdirs();

                FileOutputStream fos = new FileOutputStream(destFile);
                dest = new BufferedOutputStream(fos, 1024);
                while ((count = zis.read(data, 0, 1024)) != -1) {
                    dest.write(data, 0, count);
                }

                dest.flush();
                dest.close();
                fos.close();
            }
      }
       
  }
*/
}

