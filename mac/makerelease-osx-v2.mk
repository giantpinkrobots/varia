# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/
# Written by Nils Maier

# This make file will:
#  - Download a set of dependencies and verify the known-good hashes.
#  - Build static libraries of aria2 dependencies.
#  - Create a statically linked, aria2 release.
#    - The build will have all major features enabled, and will use
#      AppleTLS and GMP.
#  - Create a corresponding .tar.bz containing the binaries:
#  - Create a corresponding .pkg installer.
#  - Create a corresponding .dmg image containing said installer.
#
# This Makefile will also run all `make check` targets.
#
# The dependencies currently build are:
#  - zlib (compression, in particular web compression)
#  - c-ares (asynchronous DNS resolver)
#  - expat (XML parser, for metalinks)
#  - gmp (multi-precision arithmetric library, for DHKeyExchange, BitTorrent)
#  - sqlite3 (self-contained SQL database, for Firefox3 cookie reading)
#  - cppunit (unit tests for C++, framework in use by aria2 `make check`)
#
#
# To use this Makefile, do something along the lines of
#  - $ mkdir build-release
#  - $ cd build-release
#  - $ virtualenv .
#  - $ . bin/activate
#  - $ pip install sphinx-build
#  - $ ln -s ../makerelease-os.mk Makefile
#  - $ make
#
# If you haven't checkout out a release tag, you need to specify NON_RELEASE.
# $ export NON_RELEASE=1
# to generate a dist with git commit
# $ export NON_RELEASE=force
# to force this script to behave like it was on a tag.
#
# Note: This Makefile expects to be called from a git clone of aria2.
#
# Note: In theory, everything can be build in parallel, however the sub-makes
# will be called with an appropriate -j flag. Building the `deps` target in
# parallel before a general make might be beneficial, as the dependencies
# usually bottle-neck on the configure steps.
#
# Note: Of course, you need to have XCode with the command line tools
# installed for this to work, aka. a working compiler...
#
# Note: We're locally building the dependencies here, static libraries only.
# This is required, because when using brew or MacPorts, which also provide
# dynamic libraries, the linker will pick up the dynamic versions, always,
# with no way to instruct the linker otherwise.
# If you're building aria2 just for yourself and your system, using brewed
# libraries is fine as well.
#
# Note: This Makefile is riddled with mac-isms. It will not work on *nix.
#
# Note: The convoluted way to create separate arch builds and later merge them
# with lipo is because of two things:
#  1) Avoid patching c-ares, which hardcodes some sizes in its headers.
#
# Note: This Makefile uses resources from osx-package when creating the
# *.pkg and *.dmg targets

SHELL := bash

# A bit awkward, but OSX doesn't have a proper `readlink -f`.
SRCDIR := $(shell dirname $(lastword $(shell stat -f "%N %Y" $(lastword $(MAKEFILE_LIST)))))

# Same as in script-helper, but a bit easier on the eye (but more error prone)
# and Makefile compatible
BASE_VERSION = def
VERSION := $(BASE_VERSION)

# Set up compiler.
ARCH = x86_64
CC = cc
export CC
CXX = c++ -stdlib=libc++
export CXX

# Set up compiler/linker flags.
PLATFORMFLAGS ?= -mmacosx-version-min=10.10
OPTFLAGS ?= -Os
CFLAGS ?= $(PLATFORMFLAGS) $(OPTFLAGS)
export CFLAGS
CXXFLAGS ?= $(PLATFORMFLAGS) $(OPTFLAGS)
export CXXFLAGS
LDFLAGS ?= -Wl,-dead_strip
export LDFLAGS

LTO_FLAGS = -flto -ffunction-sections -fdata-sections

# Dependency versions
zlib_version = 1.2.11
zlib_hash = c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1
zlib_url = http://zlib.net/fossils/zlib-$(zlib_version).tar.gz

expat_version = 2.2.8
expat_hash = bd507cba42716ca9afe46dd3687fb0d46c09347517beb9770f53a435d2c67ea0
expat_url = https://github.com/libexpat/libexpat/releases/download/R_2_2_8/expat-2.2.8.tar.gz
expat_cflags=$(CFLAGS) $(LTO_FLAGS)
expat_ldflags=$(CFLAGS) $(LTO_FLAGS)

cares_version = 1.15.0
cares_hash = 6cdb97871f2930530c97deb7cf5c8fa4be5a0b02c7cea6e7c7667672a39d6852
cares_url = https://github.com/c-ares/c-ares/releases/download/cares-1_15_0/c-ares-1.15.0.tar.gz
cares_confflags = "--enable-optimize=$(OPTFLAGS)"
cares_cflags=$(CFLAGS) $(LTO_FLAGS)
cares_ldflags=$(CFLAGS) $(LTO_FLAGS)

sqlite_version = autoconf-3300000
sqlite_hash = e0a8cf4c7a87455e55e10413d16f358ca121ccec687fe1301eac95e2d340fc58
sqlite_url = https://sqlite.org/2019/sqlite-$(sqlite_version).tar.gz
sqlite_cflags=$(CFLAGS) $(LTO_FLAGS)
sqlite_ldflags=$(CFLAGS) $(LTO_FLAGS)

gmp_version = 6.3.0
gmp_hash = ac28211a7cfb609bae2e2c8d6058d66c8fe96434f740cf6fe2e47b000d1c20cb
gmp_url = https://ftp.gnu.org/gnu/gmp/gmp-$(gmp_version).tar.bz2
gmp_confflags = --disable-cxx --enable-assembly --with-pic --enable-fat
gmp_cflags=$(CFLAGS)
gmp_cxxflags=$(CXXFLAGS)

libgpgerror_version = 1.36
libgpgerror_hash = babd98437208c163175c29453f8681094bcaf92968a15cafb1a276076b33c97c
libgpgerror_url = https://gnupg.org/ftp/gcrypt/libgpg-error/libgpg-error-$(libgpgerror_version).tar.bz2
libgpgerror_cflags=$(CFLAGS) $(LTO_FLAGS)
libgpgerror_ldflags=$(CFLAGS) $(LTO_FLAGS)
libgpgerror_confflags = --with-pic --disable-languages --disable-doc --disable-nls

libgcrypt_version = 1.8.5
libgcrypt_hash = 3b4a2a94cb637eff5bdebbcaf46f4d95c4f25206f459809339cdada0eb577ac3
libgcrypt_url = https://gnupg.org/ftp/gcrypt/libgcrypt/libgcrypt-$(libgcrypt_version).tar.bz2
libgcrypt_confflags=--with-gpg-error-prefix=$(PWD)/arch --disable-O-flag-munging --disable-asm --disable-amd64-as-feature-detection
libgcrypt_cflags=$(PLATFORMFLAGS)
libgcrypt_cxxflags=$(PLATFORMFLAGS)

libssh2_version = 1.9.0
libssh2_hash = d5fb8bd563305fd1074dda90bd053fb2d29fc4bce048d182f96eaa466dfadafd
libssh2_url = https://www.libssh2.org/download/libssh2-$(libssh2_version).tar.gz
libssh2_cflags=$(CFLAGS) $(LTO_FLAGS)
libssh2_cxxflags=$(CXXFLAGS) $(LTO_FLAGS)
libssh2_ldflags=$(CFLAGS) $(LTO_FLAGS)
libssh2_confflags = --with-pic --without-openssl --with-libgcrypt=$(PWD)/arch --with-libgcrypt-prefix=$(PWD)/arch
libssh2_nocheck = yes


# ARCHLIBS that can be template build
ARCHLIBS = expat cares sqlite gmp libgpgerror libgcrypt libssh2
# NONARCHLIBS that cannot be template build
NONARCHLIBS = zlib


# Aria2 setup
ARIA2 := aria2-$(VERSION)
ARIA2_PREFIX := $(PWD)/$(ARIA2)
ARIA2_CONFFLAGS = \
        --enable-static \
        --disable-shared \
        --disable-metalink \
        --enable-bittorrent \
        --disable-nls \
        --with-appletls \
        --with-libgmp=$(PWD)/arch \
        --with-sqlite3=$(PWD)/arch \
        --with-libz=$(PWD)/arch \
        --with-libexpat=$(PWD)/arch \
        --with-libcares=$(PWD)/arch \
        --with-libgcrypt=$(PWD)/arch \
        --with-libssh2=$(PWD)/arch \
        --without-libuv \
        --without-gnutls \
        --without-openssl \
        --without-libnettle \
        --without-libxml2 \
        ARIA2_STATIC=yes

# Detect number of CPUs to be used with make -j
CPUS = $(shell sysctl hw.ncpu | cut -d" " -f2)

# default target
all::

# All those .PRECIOUS files, because otherwise gmake will treat them as
# intermediates and remove them when the build completes. Thanks gmake!
.PRECIOUS: %.tar.gz
%.tar.gz:
	curl -o $@ -A 'curl/0; like wget' -L \
		$($(basename $(basename $@))_url)

.PRECIOUS: %.check
%.check: %.tar.gz
	@if test "$$(shasum -a256 $< | awk '{print $$1}')" != "$($(basename $@)_hash)"; then \
		echo "Invalid $@ hash"; \
		rm -f $<; \
		exit 1; \
	fi;
	touch $@

.PRECIOUS: %.stamp
%.stamp: %.tar.gz %.check
	tar xf $<
	mv $(basename $@)-$($(basename $@)_version) $(basename $@)
	touch $@

.PRECIOUS: cares.stamp
cares.stamp: cares.tar.gz cares.check
	tar xf $<
	mv c-ares-$($(basename $@)_version) $(basename $@)
	touch $@

.PRECIOUS: libgpgerror.stamp
libgpgerror.stamp: libgpgerror.tar.gz libgpgerror.check
	tar xf $<
	mv libgpg-error-$($(basename $@)_version) $(basename $@)
	touch $@

# Using (NON)ARCH_template kinda stinks, but real multi-target pattern rules
# only exist in feverish dreams.
define NONARCH_template
$(1).build: $(1).$(ARCH).build

deps:: $(1).build

endef

.PRECIOUS: zlib.%.build
zlib.%.build: zlib.stamp
	$(eval BASE := $(basename $<))
	$(eval DEST := $(basename $@))
	$(eval ARCH := $(subst .,,$(suffix $(DEST))))
	rsync -a $(BASE)/ $(DEST)
	( cd $(DEST) && ./configure \
		--static --prefix=$(PWD)/arch \
		)
	$(MAKE) -C $(DEST) -sj$(CPUS) CFLAGS="$(CFLAGS) $(LTO_FLAGS) -arch $(ARCH)"
	$(MAKE) -C $(DEST) -sj$(CPUS) CFLAGS="$(CFLAGS) $(LTO_FLAGS) -arch $(ARCH)" check
	$(MAKE) -C $(DEST) -s install
	touch $@

$(foreach lib,$(NONARCHLIBS),$(eval $(call NONARCH_template,$(lib))))

define ARCH_template
.PRECIOUS: $(1).%.build
$(1).%.build: $(1).stamp
	$$(eval DEST := $$(basename $$@))
	$$(eval ARCH := $$(subst .,,$$(suffix $$(DEST))))
	mkdir -p $$(DEST)
	( cd $$(DEST) && ../$(1)/configure \
		--enable-static --disable-shared \
		--prefix=$(PWD)/arch \
		$$($(1)_confflags) \
		CFLAGS="$$($(1)_cflags) -arch $$(ARCH)" \
		CXXFLAGS="$$($(1)_cxxflags) -arch $$(ARCH) -std=c++11" \
		LDFLAGS="$(LDFLAGS) $$($(1)_ldflags)" \
		PKG_CONFIG_PATH=$$(PWD)/arch/lib/pkgconfig \
		)
	$$(MAKE) -C $$(DEST) -sj$(CPUS)
	if test -z '$$($(1)_nocheck)'; then $$(MAKE) -C $$(DEST) -sj$(CPUS) check; fi
	$$(MAKE) -C $$(DEST) -s install
	touch $$@

$(1).build: $(1).$(ARCH).build

deps:: $(1).build

endef

$(foreach lib,$(ARCHLIBS),$(eval $(call ARCH_template,$(lib))))

.PRECIOUS: aria2.%.build
aria2.%.build: zlib.%.build expat.%.build gmp.%.build cares.%.build sqlite.%.build libgpgerror.%.build libgcrypt.%.build libssh2.%.build
	$(eval DEST := $$(basename $$@))
	$(eval ARCH := $$(subst .,,$$(suffix $$(DEST))))
	mkdir -p $(DEST)
	( cd $(DEST) && ../$(SRCDIR)/configure \
		--prefix=$(ARIA2_PREFIX) \
		--bindir=$(PWD)/$(DEST) \
		--sysconfdir=/etc \
		$(ARIA2_CONFFLAGS) \
		CFLAGS="$(CFLAGS) $(LTO_FLAGS) -arch $(ARCH) -I$(PWD)/arch/include" \
		CXXFLAGS="$(CXXFLAGS) $(LTO_FLAGS) -arch $(ARCH) -I$(PWD)/arch/include" \
		LDFLAGS="$(LDFLAGS) $(CXXFLAGS) $(LTO_FLAGS) -L$(PWD)/arch/lib" \
		PKG_CONFIG_PATH=$(PWD)/arch/lib/pkgconfig \
		)
	$(MAKE) -C $(DEST) -sj$(CPUS)
	# $(MAKE) -C $(DEST) -sj$(CPUS) check
	# Check that the resulting executable is Position-independent (PIE)
	otool -hv $(DEST)/src/aria2c | grep -q PIE
	$(MAKE) -C $(DEST) -sj$(CPUS) install-strip
	touch $@

aria2.build: aria2.$(ARCH).build
	mkdir -p $(ARIA2_PREFIX)/bin
	cp -f aria2.$(ARCH)/aria2c $(ARIA2_PREFIX)/bin/aria2c
	arch -64 $(ARIA2_PREFIX)/bin/aria2c -v
	touch $@

all:: aria2.build

clean:
	rm -rf *aria2*

.PHONY: all multi clean
