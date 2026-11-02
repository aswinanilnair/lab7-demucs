# RustFS README

We use [RustFS](https://github.com/rustfs/rustfs) as the object store in place of Min.io. It speaks the S3 API, so the REST server and worker connect to it with `boto3` using `S3_ENDPOINT`, `S3_ACCESS_KEY` and `S3_SECRET_KEY`.

`rustfs.yaml` deploys a single pod and a service called `rustfs` in the `default` namespace, so no `ExternalName` service is needed. The credentials are in the `rustfs-credentials` secret in that file.

Port 9000 is the S3 API and port 9001 is the web console. `deploy-local-dev.sh` forwards both to your computer.

The data is stored in an `emptyDir`, so deleting the pod deletes the buckets and their contents. The REST server and worker create the `queue` and `output` buckets when they start, so restart them if you delete the RustFS pod.
