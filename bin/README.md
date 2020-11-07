# UltraSync Development Tools

This directory just contains some tools that are useful when developing with UltraSync.  It is presumed that you've set yourself up with a working development environment before using the tools identified here:

```bash
# Using pip, setup a working development environment:
pip install -r requirements.txt
```

The tools are as follows:

- :gear: `ultrasync`: This effectively acts as the `ultrasync` tool would once UltraSync has been installed into your environment.  However `ultrasync` uses the branch you're working in.  So if you added a new Notification service, you can test with it as you would easily.  `ultrasync` takes all the same parameters as the `ultrasync` tool does.

    ```bash
    # simply make your code changes to ultrasync and test it out:
    ./bin/ultrasync -c /path/to/your/config.conf --watch
    ```

- :gear: `test.sh`: This allows you to just run the unit tests associated with this project.  You can optionally specify a _keyword_ as a parameter and the unit tests will specifically focus on a single test.  This is useful when you need to debug something and don't want to run the entire fleet of tests each time.  e.g:

   ```bash
   # Run all tests:
   ./bin/tests.sh

   # Run just the tests associated with the rest framework:
   ./bin/tests.sh rest

   # Run just the UltraSync config related unit tests
   ./bin/tests.sh config
   ```

- :gear: `checkdone.sh`: This script just runs a lint check against the code to make sure there are no PEP8 issues and additionally runs a full test coverage report.

   ```bash
   # Perform PEP8 and test coverage check on all code and reports
   # back. It's called 'checkdone' because it checks to see if you're
   # actually done with your code commit or not. :)
   ./bin/checkdone.sh
   ```

You can optionally just update your path to include this `./bin` directory and call the scripts that way as well. Hence:
```bash
# Update the path to include the bin directory:
export PATH="$(pwd)/bin:$PATH"

# Now you can call the scripts identified above from anywhere...
```

