===========================
Asterisk Plus Documentation
===========================
You can find setup installation **instructions** at https://docs.odoopbx.com.

**Paid installation** is available at https://odoopbx.com/paid-installation.


Instance registration and subscription
======================================
In order to use this application you must register your Odoo instance in our billing system.
Check out the Instance Registration Guide: https://scribehow.com/shared/Register_your_Odoo_instance__yczyIZtZQZycdXLSSlp6NQ

After the registration you should update your Payment Profile and add your payment source that will be
used to pay for the subscription: https://scribehow.com/shared/Updating_Payment_Profile_and_Subscribing_to_a_product__3_GiJbTBSLmkCmmr5fy6VQ

After that you click the ``SUBSCRIBE`` button to begin your subscription or click ``FREE TEST 14 DAYS`` to start
the product evaluation. If you decide to opt-out from the product you must cancel your trial subscription
before the trial period ends otherwise subscription will start automatically.

ChangeLog
=========
3.2
---
* FastAGI support added. 
* User's personal numbers feature added.

3.1
---
* New option ``Server -> Starting Exten`` added. This allows to define starting extension when ``Autocreate PBX Users`` is enabled.
* Fixed a bug with phone format.
* Small UX improvements.
* Added automatic user names conversion to english letters on SIP users generation.
* Added automatic callerid number setting on outbound calls.
* Added phone and mobile fields to the PBX user form.

3.0
---
* Launch of the new billing system with pay-as-you-go pricing model. Now subscription management is 
  built directly into the application.
* Added active calls widget for getting quick information on current calls from any place.
* The Asterisk Plus Agent is not installed on the Asterisk server and has a auto configuration initialization.
  Please contact technical support to assist you with migration!
* Added database index for call reference in order to speed up things on large deployments.
* Many other small fixes and improvements.

2.5
---
* Added an option to disable phone formatting to leave numbers as is. Useful for Arabic and other BiDi languages.

2.4
---
* Automatic Agent connection implemented.
* Call direction detection improvement.

2.3
---
* Search partner by number refactoring. Added an option *Search number operation* that allows partial 
  number search. This is used when number field is used to store several phone numbers separated with a '/'.
* Call recording MP3 conversion moved to the Agent side to reduce Odoo worker's load.

2.2
---
* Added support for OpenVPN. Now Agent can make connection to Asterisk server using OpenVPN.

2.1
---
* Added call recording transcript & ChatGPT summary feature.

2.0
---
* 2.0 release.