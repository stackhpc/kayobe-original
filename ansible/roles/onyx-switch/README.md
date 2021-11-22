Onyx Switch
=============

This role configures Mellanox Onyx switches using the `mellanox.onyx` Ansible
collection.  It provides a fairly minimal abstraction of the configuration
interface provided by the `onyx_config` module, allowing for application of
arbitrary switch configuration options.

Requirements
------------

The Mellanox Onyx Ansible collection require Onyx 3.6.8130 or later.

The switches should be configured to allow SSH access.

Role Variables
--------------

`onyx_switch_config` is a list of configuration lines to apply to the switch,
and defaults to an empty list.

`onyx_switch_interface_config` contains interface configuration. It is a dict
mapping switch interface names to configuration dicts. Each dict may contain
the following items:

- `description` - a description to apply to the interface.
- `config` - a list of per-interface configuration.

Dependencies
------------

mellanox.onyx collection

Example Playbook
----------------

The following playbook configures hosts in the `onyx-switches` group.
It assumes host variables for each switch holding the host, username and
passwords.  It applies global configuration for LLDP, and enables two
10G ethernet interfaces as switchports.

    ---
    - name: Ensure Onyx switches are configured
      hosts: onyx-switches
      gather_facts: no
      roles:
        - role: onyx-switch
          onyx_switch_provider:
            host: "{{ switch_host }}"
            username: "{{ switch_user }}"
            password: "{{ switch_password }}"
            transport: cli
            authorize: yes
            auth_pass: "{{ switch_auth_pass }}"
            timeout: 60
          onyx_switch_config:
            - "lldp run"
            - "lldp tlv-select system-name"
            - "lldp tlv-select management-address"
            - "lldp tlv-select port-description"
          onyx_switch_interface_config:
            Et4/5:
              description: server-1
              config:
                - "no shutdown"
                - "switchport"
            Et4/7:
              description: server-2
              config:
                - "no shutdown"
                - "switchport"

Author Information
------------------

- Piotr Parczewski (<piotr@stackhpc.com>)

Based on the arista-switch role by Stig Telfer (<stig@stackhpc.com>)
