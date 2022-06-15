This worker will accept a file and save it with the key of format "20220-06-14_db.sqlite3", overwriting any file with the same name. It does not check that the posted file is actually an sqlite database. We get 10GB of storage on the free tier, our DB is less than 2MB.

Usage: `curl https://backup.erudo.workers.dev -X POST --header "X-Custom-Auth-Key: AUTH_KEY_SECRET" --data-binary '@db.sqlite3'`

To develop, first set up wrangler:
`npm i -g wrangler`
`wrangler login`

Make changes, then run
`wrangler develop`

The develop version uses the bucket named `preview-backup`

If you're happy with your changes:
`wrangler publish`

To change the `AUTH_KEY_SECRET`:
`wrangler secret put AUTH_KEY_SECRET`