mcsoda - sugary streaming load generator for key-value stores.

Usage instructions
------------------

    usage: ./mcsoda.py [memcached[-binary|-ascii]://][user[:pswd]@]host[:port] [key=val]*

      default protocol = memcached-binary://
      default port     = 11211

    examples: ./mcsoda.py memcached-binary://127.0.0.1:11211 max-items=1000000 json=1
              ./mcsoda.py memcached://127.0.0.1:11211
              ./mcsoda.py 127.0.0.1:11211
              ./mcsoda.py 127.0.0.1
              ./mcsoda.py my-test-bucket@127.0.0.1
              ./mcsoda.py my-test-bucket:MyPassword@127.0.0.1

    optional key=val's and their defaults:
      backoff-factor     = 2.0   Exponential backoff factor on ETMPFAIL errors.
      batch              = 100   Batch/pipeline up this # of commands per server.
      doc-cache          = 1     When 1, cache docs; faster, but uses O(N) memory.
      doc-gen            = 1     When 1 and doc-cache, pre-generate docs at start.
      exit-after-creates = 0     Exit after max-creates is reached.
      expiration         = 0     Expiration time parameter for SET's
      histo-precision    = 1     Precision of histogram bins.
      hot-shift          = 0     # of keys/sec that hot item subset should shift.
      json               = 1     Use JSON documents. 0 to generate binary documents.
      max-creates        = -1    Max # of creates; defaults to max-items.
      max-items          = -1    Max # of items; default 100000.
      max-ops            = 0     Max # of ops before exiting. 0 means keep going.
      max-ops-per-sec    = 0     When >0, max ops/second target performance.
      min-value-size     = 10    Min value size (bytes) for SET's; comma-separated.
      prefix             =       Prefix for every item key.
      ratio-arpas        = 0.0   Fraction of SET non-DELETE'S to be 'a-r-p-a' cmds.
      ratio-creates      = 0.1   Fraction of SET's that should create new items.
      ratio-deletes      = 0.0   Fraction of SET updates that shold be DELETE's.
      ratio-expirations  = 0.0   Fraction of SET's that use the provided expiration.
      ratio-hot          = 0.2   Fraction of items to have as a hot item subset.
      ratio-hot-gets     = 0.95  Fraction of GET's that hit the hot item subset.
      ratio-hot-sets     = 0.95  Fraction of SET's that hit the hot item subset.
      ratio-misses       = 0.05  Fraction of GET's that should miss.
      ratio-sets         = 0.1   Fraction of requests that should be SET's.
      report             = 40000 Emit performance output after this many requests.
      threads            = 1     Number of client worker threads to use.
      time               = 0     Stop after this many seconds if > 0.
      vbuckets           = 0     When >0, vbucket hash in memcached-binary protocol.
      cur-arpas          = 0     # of add/replace/prepend/append's (a-r-p-a) cmds.
      cur-base           = 0     Base of numeric key range. 0 by default.
      cur-creates        = 0     Number of sets that were creates.
      cur-deletes        = 0     Number of deletes already done.
      cur-gets           = 0     Number of gets already done.
      cur-items          = 0     Number of items known to already exist.
      cur-sets           = 0     Number of sets already done.

      TIP: min-value-size can be comma-separated values: min-value-size=10,256,1024

More info
---------

Presentation (pdf) available at: https://github.com/couchbaselabs/mcsoda/blob/master/doc/mcsoda.pdf?raw=true




