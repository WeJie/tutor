.. _k8s:

Aliyun Kubernetes deployment
=====================

::

           _       _              __            _                  
      __ _| |_ __ | |__   __ _   / _| ___  __ _| |_ _   _ _ __ ___ 
     / _` | | '_ \| '_ \ / _` | | |_ / _ \/ _` | __| | | | '__/ _ \
    | (_| | | |_) | | | | (_| | |  _|  __/ (_| | |_| |_| | | |  __/
     \__,_|_| .__/|_| |_|\__,_| |_|  \___|\__,_|\__|\__,_|_|  \___|
            |_|                                                    

Aliyun Kubernetes deployment is currently an alpha feature, and we are hard at work to make it 100% reliable 🛠️ If you are interested in deploying Open edX to Kubernetes, please get in touch! Your input will be much appreciated.

Requirements
------------
- One aliyun Kubernetes cluster
- Aliyun NAS(Network Attached Storage) service
- Domain name for accessing openedx from public network


Quickstart
----------

Launch the platform on k8s in 1 click::

    tutor aliyun quickstart


Add ALIYUN_STORAGE_SERVER to config.yml
Add ALIYUN_NAMESPACE to config.yml

All Kubernetes resources are associated to ALIYUN_NAMESPACE of conifg.yml.


Upgrading
---------

After pulling updates from the Tutor repository, you can apply changes with::

    tutor aliyun stop
    tutor aliyun start


To Do list
----------
- Can't delete PersistentVolume via `tutor aliyun delete`
- Better way to deal with ALIYUN_STORAGE_SERVER and ALIYUN_NAMESPACE
- Support specify namspace via command line argument
- Generate random namspace for every different deployment


Missing features
----------------

For now, the following features from the local deployment are not supported:

- HTTPS certificates
- Xqueue
- Student notes
