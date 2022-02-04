# VK image scraper

This app allow you download all images from your VK-conversations data copy

## How get your VK-data copy
1. Go to [VK data protection section](https://vk.com/data_protection?section=rules)
2. Find section `Download Your Information` and click button `Request data copy`
3. Wait until your archive will be ready and download it
4. Unpack archive


## Run application
In command prompt go to app root directory and run

`python app/scrapper.py <MESSAGES_DIR> <OUT_DIR> --threads <NUM_OF_THREAD>`

where
```
  MESSAGES_DIR  Path to your messages directory in data copy  [required]
  [OUT_DIR]     Path to save out data  [default: out]
  
  --threads INTEGER     Number of parallel threads to save data  [default: 4]
```

### Run by docker

You can use docker to run application

1. Build docker image by `docker-compose build`
2. Copy directory `messages` to root application directory
3. Run `docker-compose run --rm app python app/scraper.py messages`