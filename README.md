# Image Similarity Search

Finds groups of similar images and organizes them into folders for subsequent deletion.  
(Method for searching using embeddings is available in the `by_embeddings` branch)

## Culling Process for Similar Images

1) Edit the `config.py` file.

2) Find duplicates (main function):
```bash
python main.py --action find
```
As a result, you will get sets of folders, each containing a group of similar images. The name of each file is the encoded full path to the original file.

3) Manually select the images that are not needed by deleting them from the folders.

4) After deleting, run:
```bash
python main.py --action check-deleted
```
As a result, you will get a file containing the full paths to the images that need to be deleted.

5) Delete the original files:
```bash
python main.py --action cleanup
```

### Workflow Example

**Situation**: You have 3 similar photos of one event:
- `/photos/vacation1.jpg` (best quality)
- `/photos/vacation1_copy.jpg` (duplicate)
- `/photos/vacation1_old.jpg` (poor quality)

**Step 1**: Run `python main.py --action find`
- The program finds these 3 files as similar.
- It copies them to `/output/1/photos_vacation1.jpg`, `/output/1/photos_vacation1_copy.jpg`, and `/output/1/photos_vacation1_old.jpg`.

**Step 2**: Manual sorting in `/output/1/`
- You review the files and decide to keep only `photos_vacation1.jpg` (the best quality one).
- You delete `photos_vacation1_copy.jpg` and `photos_vacation1_old.jpg` from the folder.

**Step 3**: Run `python main.py --action check-deleted`
- The program sees that `photos_vacation1_copy.jpg` and `photos_vacation1_old.jpg` have been deleted.
- It writes the original paths to `to_delete.txt`: `/photos/vacation1_copy.jpg` and `/photos/vacation1_old.jpg`.

**Step 4**: Run `python main.py --action cleanup`
- The program deletes the original files `/photos/vacation1_copy.jpg` and `/photos/vacation1_old.jpg`.
- Only `/photos/vacation1.jpg` remains in the source folder.

## How It Works

1.  **File Search**: The program recursively scans the specified folder.
2.  **Image Processing**: Each image is:
    - Loaded and checked for validity.
    - Converted to grayscale (to remove color influence).
    - Resized to a standard size of 1024x1024.
    - A hash is calculated for comparison.
3.  **Similarity Search**: The hashes of all images are compared.
4.  **Grouping**: Similar images are grouped together.
5.  **Saving**: Each group is saved into a separate numbered folder.
6.  **Tracking**: File mapping information is saved in the `INFO_FILE`.

## Result Format

### Folder Structure
```
output/
├── 1/
│   ├── home_user_photos_image1.jpg
│   ├── home_user_vacation_image1_copy.jpg
│   └── home_user_backup_image1_duplicate.png
├── 2/
│   ├── home_user_photos_image2.jpg
│   └── home_user_work_similar_image.jpg
├── 3/
│   └── ...
├── info.txt              # Mapping of original paths to saved files
└── to_delete.txt         # List of files to delete
```

### Tracking Files

**info.txt** (JSON format):
```json
{
  "/home/user/photos/image1.jpg": "/output/1/home_user_photos_image1.jpg",
  "/home/user/vacation/image1_copy.jpg": "/output/1/home_user_vacation_image1_copy.jpg"
}
```

**to_delete.txt** (line by line):
```
/home/user/photos/image1.jpg
/home/user/vacation/image1_copy.jpg
```