# Manual Seats

This is a plugin for [pretix](https://github.com/pretix/pretix).

Manually assign tickets to seats.

## Development setup

1.  Make sure that you have a working [pretix development
    setup](https://docs.pretix.eu/en/latest/development/setup.html).
2.  Clone this repository.
3.  Activate the virtual environment you use for pretix development.
4.  Execute `python setup.py develop` within this directory to register
    this application with pretix\'s plugin registry.
5.  Execute `make` within this directory to compile translations.
6.  Restart your local pretix server. You can now use the plugin from
    this repository for your events by enabling it in the \'plugins\'
    tab in the settings.

This plugin has CI set up to enforce a few code style rules. To check
locally, you need these packages installed:
```bash
pip install flake8 isort black
```
    

To check your plugin for rule violations, run:
```bash
black --check .
isort -c .
flake8 .
```

You can auto-fix some of these issues by running:
```bash
isort .
black .
```

To automatically check for these issues before you commit, you can run
`.install-hooks`.

## License

Copyright 2023 Moritz Lerch, Mark Oude Elberink

Released under the terms of the Apache License 2.0

## Internal Usage
```dockerfile
FROM ghcr.io/abi23ohm/pretix-manualseats as pretix_manualseats

FROM pretix...

...

COPY --from=pretix_manualseats /plugins/pretix_manualseats /plugins/pretix_manualseats
RUN pip install -e /plugins/pretix_manualseats
```