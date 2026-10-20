# KUKA iiwa meshes

The eight OBJ meshes and `model.urdf` come from Bullet's `data/kuka_iiwa` directory at commit
`d3afe76132fc76b0f9b2359cbaef47a3766e7fbb`:

https://github.com/bulletphysics/bullet3/tree/d3afe76132fc76b0f9b2359cbaef47a3766e7fbb/data/kuka_iiwa

The URDF identifies the original model as `rtkg/lbr_iiwa` and contains its BSD license notice.
`BULLET_LICENSE.txt` preserves Bullet's repository license. The meshes are unmodified; the Session
examples load them as metres and apply the URDF joint frames through the Session tree.
