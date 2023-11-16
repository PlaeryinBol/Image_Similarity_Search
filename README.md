# Search for too similar images by their embeddings

## Project Overview
Sometimes I have a directory with many images that contains a lot of similar images (with different names) among them. I use the distance between embeddings as a measure of similarity to find such images via DBSCAN.

## Usage
Specify all the required values in the `config.py`, then run
```bash
$ python main.py
```
As a result, groups of images that are similar to each other will be placed in separate folders in the *DIR_FOR_SIMILARS* folder.

Depending on how similar images you want to find, you will need to choose your own *DISTANCE_THRESHOLD* or *DBSCAN_EPSILON* parameter value. This can be easily done by looking at the search results in the *DIR_FOR_SIMILARS* folder.

## Examples
By comparing embeddings, you can find similar images like this that are similar in meaning, and if necessary, remove semantic duplicates.

<p>
  <img src="./images/similar_1.jpg" width="200" />
  <img src="./images/similar_2.jpg" width="450" />
</p>

<p>
  <img src="./images/similar_3.jpg" width="200" />
  <img src="./images/similar_4.jpg" width="450" />
</p>