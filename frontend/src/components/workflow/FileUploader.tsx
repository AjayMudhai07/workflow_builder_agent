"use client";

import React, { useCallback, useState } from "react";
import { Upload, X, FileText, AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

interface UploadedFile {
  file: File;
  id: string;
  rows?: number;
  columns?: number;
  error?: string;
}

interface FileUploaderProps {
  maxFiles?: number;
  maxSizeMB?: number;
  acceptedTypes?: string[];
  onFilesChange: (files: File[]) => void;
  className?: string;
}

export function FileUploader({
  maxFiles = 5,
  maxSizeMB = 100,
  acceptedTypes = [".csv", ".xlsx"],
  onFilesChange,
  className,
}: FileUploaderProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    // Check file type
    const fileExt = "." + file.name.split(".").pop()?.toLowerCase();
    if (!acceptedTypes.includes(fileExt)) {
      return `Invalid file type. Accepted: ${acceptedTypes.join(", ")}`;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSizeMB) {
      return `File too large. Max size: ${maxSizeMB}MB`;
    }

    return null;
  };

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files) return;

      setError(null);

      const filesArray = Array.from(files);

      // Check max files limit
      if (uploadedFiles.length + filesArray.length > maxFiles) {
        setError(`Maximum ${maxFiles} files allowed`);
        return;
      }

      const newUploadedFiles: UploadedFile[] = [];

      for (const file of filesArray) {
        const validationError = validateFile(file);

        if (validationError) {
          setError(validationError);
          continue;
        }

        // Analyze CSV (basic preview - count lines)
        let rows: number | undefined;
        try {
          if (file.name.endsWith(".csv")) {
            const text = await file.text();
            rows = text.split("\n").length - 1; // Subtract header
          }
        } catch (err) {
          console.error("Error analyzing file:", err);
        }

        newUploadedFiles.push({
          file,
          id: `${file.name}-${Date.now()}`,
          rows,
        });
      }

      const updatedFiles = [...uploadedFiles, ...newUploadedFiles];
      setUploadedFiles(updatedFiles);
      onFilesChange(updatedFiles.map((uf) => uf.file));
    },
    [uploadedFiles, maxFiles, maxSizeMB, acceptedTypes, onFilesChange]
  );

  const removeFile = (id: string) => {
    const updatedFiles = uploadedFiles.filter((f) => f.id !== id);
    setUploadedFiles(updatedFiles);
    onFilesChange(updatedFiles.map((uf) => uf.file));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Drop Zone */}
      <Card
        className={cn(
          "border-2 border-dashed transition-colors cursor-pointer",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
          <Upload
            className={cn(
              "w-12 h-12 mb-4 transition-colors",
              isDragging ? "text-primary" : "text-muted-foreground"
            )}
          />
          <h3 className="text-lg font-semibold mb-2">
            Drop CSV files here or click to browse
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            Supported: {acceptedTypes.join(", ")} • Max {maxSizeMB}MB per file
          </p>
          <Button type="button" variant="secondary" size="sm">
            Browse Files
          </Button>
          <input
            id="file-input"
            type="file"
            multiple
            accept={acceptedTypes.join(",")}
            onChange={handleFileInput}
            className="hidden"
          />
        </div>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">
            Uploaded Files ({uploadedFiles.length})
          </h4>
          {uploadedFiles.map((uploadedFile) => (
            <Card key={uploadedFile.id} className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <FileText className="w-5 h-5 text-primary" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {uploadedFile.file.name}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="secondary" className="text-xs">
                        {(uploadedFile.file.size / 1024).toFixed(1)} KB
                      </Badge>
                      {uploadedFile.rows !== undefined && (
                        <Badge variant="outline" className="text-xs">
                          ~{uploadedFile.rows.toLocaleString()} rows
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(uploadedFile.id);
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
