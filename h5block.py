import h5py
import inspect


class _DsetWrap(object):
    def __init__(self, file_descriptor, dset_descriptor):
        self.fd = file_descriptor
        self.ds = dset_descriptor
        self.members = [m[0] for m in inspect.getmembers(self.ds)]

    def __str__(self):
        return "<h5block "+self.ds.__str__()+", maxshape {}>".format(self.ds.maxshape)

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, attr):
        if attr in self.members:
            return self.ds.__getattribute__(attr)
        else:
            raise AttributeError('')

    def __getitem__(self, key):
        return self.ds.__getitem__(key)

    def __setitem__(self, key, value):
        return self.ds.__setitem__(key, value)

    def extend(self, data, axis=None):
        maxshape = self.ds.maxshape
        curr_shape = self.ds.shape
        extd_shape = data.shape
        if len(curr_shape) != len(extd_shape):
            raise ValueError('Number of axes does not match with the original data')

        if axis is None:
            if maxshape.count(None) > 1:
                raise ValueError('You need to specify the axis when there are multiple extendable axes')
            axis = maxshape.index(None) # first extendable axis

        for i in xrange(len(curr_shape)):
            if i!=axis and curr_shape[i] != extd_shape[i]:
                raise ValueError('Dimension {} does not match with the original data'.format(i))
        
        new_shape = list(curr_shape)
        new_shape[axis] += extd_shape[axis]
        self.ds.resize(tuple(new_shape))

        slcs = [slice(None,None,None) for s in xrange(len(curr_shape))]
        slcs[axis] = slice(curr_shape[axis], new_shape[axis], None)
        self.ds[tuple(slcs)] = data
        self.fd.flush()


class _FileWrap(object):
    def __init__(self, file_descriptor):
        self.fd = file_descriptor
        self.members = [m[0] for m in inspect.getmembers(self.fd)]

    def __str__(self):
        return "<h5block "+self.fd.__str__()+" >"

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, attr):
        if attr in self.members:
            return self.fd.__getattribute__(attr)
        else:
            raise AttributeError('')

    def create_dataset(self, *args, **kwargs):
        if 'axis' in kwargs.keys(): # axis is given
            axis = kwargs['axis']
            kwargs.pop('axis', None)
            if not isinstance(axis, list):
                axis = [axis]
            
            if len(args) == 1:
                assert('data' in kwargs.keys())
                maxshape = list(kwargs['data'].shape)
            elif len(args) == 2:
                maxshape = list(args[1])
            else:
                print "Not permitted"
                return

            for i in axis:
                maxshape[i] = None
            kwargs['maxshape'] = tuple(maxshape)

        ds = self.fd.create_dataset(*args, **kwargs)
        self.fd.flush()
        dw = _DsetWrap(self.fd, ds)
        return dw

def File(*args, **kwargs):
    fd = h5py.File(*args, **kwargs)
    fw = _FileWrap(fd)
    return fw



