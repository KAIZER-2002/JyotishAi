"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { User, Shield, AlertTriangle, Edit2, X, Check, Camera, Compass } from "lucide-react";
import { useProfile } from "@/hooks/useProfile";
import { profileSchema, ProfileFormData } from "@/validations/profile";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { toast } from "sonner";
import { useAuthStore } from "@/store/authStore";
import { LocationAutocomplete } from "@/components/ui/LocationAutocomplete";

// Common timezones for Vedic Astrology calculations
const TIMEZONES = [
  "Asia/Kolkata",
  "America/New_York",
  "Europe/London",
  "Asia/Singapore",
  "Australia/Sydney",
  "America/Los_Angeles",
  "Europe/Paris",
  "Asia/Dubai",
  "Asia/Tokyo",
];

// Ayanamsas
const AYANAMSAS = [
  { value: "Lahiri", label: "Lahiri" },
  { value: "Raman", label: "Raman" },
  { value: "Krishnamurti", label: "Krishnamurti" },
  { value: "True Chitra", label: "True Chitra" },
];

export default function ProfilePage() {
  const router = useRouter();
  const { profile, isLoading, isError, error, updateProfile, isSaving, uploadAvatar, isUploading } = useProfile();
  const { user: authUser, setUser } = useAuthStore();
  const [isEditMode, setIsEditMode] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const {
    register,
    handleSubmit,
    control,
    reset,
    getValues,
    setValue,
    formState: { errors, isDirty },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: "",
      timezone: "Asia/Kolkata",
      date_of_birth: "",
      time_of_birth: "",
      birth_place: "",
      latitude: "",
      longitude: "",
      ayanamsa: "Lahiri",
      gender: "",
    },
  });


  // Load default form values once profile query resolves
  useEffect(() => {
    if (profile) {
      const formattedValues: ProfileFormData = {
        full_name: profile.full_name || "",
        timezone: profile.timezone || "Asia/Kolkata",
        date_of_birth: profile.date_of_birth || "",
        time_of_birth: profile.time_of_birth
          ? profile.time_of_birth.substring(0, 5) // truncate HH:MM:SS to HH:MM if necessary
          : "",
        birth_place: profile.birth_place || "",
        latitude: profile.latitude !== null && profile.latitude !== undefined ? String(profile.latitude) : "",
        longitude: profile.longitude !== null && profile.longitude !== undefined ? String(profile.longitude) : "",
        ayanamsa: profile.ayanamsa || "Lahiri",
        gender: profile.gender || "",
      };
      reset(formattedValues);
    }
  }, [profile, reset]);

  // Handle browser warning if navigating away with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty && isEditMode) {
        e.preventDefault();
        e.returnValue = "You have unsaved changes. Are you sure you want to leave?";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isDirty, isEditMode]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
        <div className="flex items-center gap-4">
          <Skeleton className="size-20 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-80 w-full rounded-2xl" />
          <Skeleton className="h-80 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Profile Load Failed</AlertTitle>
          <AlertDescription>
            {error instanceof Error ? error.message : "Failed to load user profile."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const handleFormSubmit = (data: ProfileFormData) => {
    // Partially construct update object based on what changed (or pass everything cleanly)
    const updatedFields = {
      full_name: data.full_name || null,
      timezone: data.timezone || null,
      date_of_birth: data.date_of_birth || null,
      time_of_birth: data.time_of_birth ? `${data.time_of_birth}:00` : null, // format as HH:MM:SS
      birth_place: data.birth_place || null,
      latitude: data.latitude ? parseFloat(data.latitude) : null,
      longitude: data.longitude ? parseFloat(data.longitude) : null,
      ayanamsa: data.ayanamsa || null,
      gender: data.gender || null,
    };

    updateProfile(updatedFields, {
      onSuccess: (updated) => {
        setIsEditMode(false);
        // Sync local auth store user name for Layout display consistency
        if (authUser) {
          setUser({
            ...authUser,
            name: updated.full_name || authUser.name,
          });
        }
        toast.success("Profile updated successfully!");
        // We stay on the profile page instead of redirecting abruptly.
      },
    });
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 1024 * 1024) {
      toast.error("Avatar size must be less than 1MB");
      return;
    }

    try {
      // Local preview immediately for optimistic UI
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === "string") {
          setAvatarPreview(reader.result);
        }
      };
      reader.readAsDataURL(file);

      // Perform actual upload via API abstraction (no Base64 in database)
      await uploadAvatar(file);
    } catch {
      setAvatarPreview(profile?.avatar_url || null);
    }
  };

  const handleRemoveAvatar = async () => {
    const confirmRemove = window.confirm("Are you sure you want to remove your avatar?");
    if (!confirmRemove) return;

    try {
      setAvatarPreview(null);
      await updateProfile({ avatar_url: null });
    } catch {
      setAvatarPreview(profile?.avatar_url || null);
    }
  };

  const handleCancel = () => {
    if (isDirty) {
      const confirmCancel = window.confirm("You have unsaved changes. Discard them?");
      if (!confirmCancel) return;
    }
    setIsEditMode(false);
    if (profile) {
      reset({
        full_name: profile.full_name || "",
        timezone: profile.timezone || "Asia/Kolkata",
        date_of_birth: profile.date_of_birth || "",
        time_of_birth: profile.time_of_birth
          ? profile.time_of_birth.substring(0, 5)
          : "",
        birth_place: profile.birth_place || "",
        latitude: profile.latitude !== null && profile.latitude !== undefined ? String(profile.latitude) : "",
        longitude: profile.longitude !== null && profile.longitude !== undefined ? String(profile.longitude) : "",
        ayanamsa: profile.ayanamsa || "Lahiri",
        gender: profile.gender || "",
      });
      setAvatarPreview(profile.avatar_url);
    }
  };

  const initials = profile?.full_name
    ? profile.full_name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : profile?.username?.slice(0, 2).toUpperCase() || "US";

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
      {/* Header Profile Section */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b border-white/10">
        <div className="flex flex-col sm:flex-row items-center gap-4 text-center sm:text-left">
          <div className="flex flex-col items-center gap-2">
            <div className="relative group">
              <Avatar className="size-24 border-2 border-primary/20 bg-primary/10">
                <AvatarImage src={avatarPreview || undefined} alt={profile?.full_name || "User Avatar"} />
                <AvatarFallback className="text-xl font-bold bg-primary/10 text-primary">
                  {initials}
                </AvatarFallback>
              </Avatar>
              {isEditMode && (
                <button
                  type="button"
                  disabled={isUploading}
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer focus:opacity-100 disabled:opacity-50"
                  aria-label="Upload avatar image"
                >
                  {isUploading ? (
                    <span className="size-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Camera className="size-6 text-white" />
                  )}
                </button>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleAvatarChange}
              />
            </div>
            {isEditMode && avatarPreview && (
              <button
                type="button"
                onClick={handleRemoveAvatar}
                className="text-[11px] text-destructive hover:underline font-medium cursor-pointer"
                aria-label="Remove avatar image"
              >
                Remove Avatar
              </button>
            )}
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              {profile?.full_name || profile?.username || "Vedic Practitioner"}
            </h1>
            <p className="text-sm text-muted-foreground">{profile?.email}</p>
            <div className="flex items-center gap-2 mt-1 justify-center sm:justify-start">
              <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                <Shield className="size-3" />
                {profile?.is_superuser ? "Administrator" : "Standard User"}
              </span>
            </div>
          </div>
        </div>

        <div>
          {!isEditMode ? (
            <Button
              type="button"
              onClick={() => setIsEditMode(true)}
              className="gap-2"
              aria-label="Edit profile details"
            >
              <Edit2 className="size-4" />
              Edit Profile
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={isSaving || isUploading}
                className="gap-2"
              >
                <X className="size-4" />
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSaving || isUploading}
                className="gap-2 bg-success text-success-foreground hover:bg-success/90"
              >
                {isSaving ? (
                  <span className="size-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Check className="size-4" />
                )}
                Save Changes
              </Button>
            </div>
          )}
        </div>
      </div>

      {isDirty && isEditMode && (
        <Alert variant="default" className="border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-500">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <AlertTitle className="font-semibold">Unsaved Changes</AlertTitle>
          <AlertDescription>
            You have modified your profile details. Click &ldquo;Save Changes&rdquo; to persist them.
          </AlertDescription>
        </Alert>
      )}

      {/* Main Form Fields */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Personal Details */}
        <Card className="glass-card border-white/10 bg-sidebar/5 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              <User className="size-5 text-primary" /> Personal Information
            </CardTitle>
            <CardDescription>Update your personal identity details.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Legal Name</Label>
              <Input
                id="full_name"
                disabled={!isEditMode || isSaving || isUploading}
                placeholder="Enter your full name"
                {...register("full_name")}
                className="bg-background/40"
              />
              {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                disabled={true}
                value={profile?.username || ""}
                readOnly
                className="bg-muted/40 cursor-not-allowed opacity-80"
              />
              <p className="text-[10px] text-muted-foreground">Username cannot be changed directly.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                disabled={true}
                value={profile?.email || ""}
                readOnly
                className="bg-muted/40 cursor-not-allowed opacity-80"
              />
              <p className="text-[10px] text-muted-foreground">Email address cannot be changed directly.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="timezone">Calculation Timezone</Label>
              <Controller
                name="timezone"
                control={control}
                render={({ field }) => (
                  <div className="flex gap-2">
                    <Input
                      id="timezone"
                      disabled={!isEditMode || isSaving || isUploading}
                      placeholder="e.g. Asia/Kolkata"
                      {...field}
                      value={field.value || ""}
                      className="bg-background/40"
                    />
                  </div>
                )}
              />
              {errors.timezone && <p className="text-xs text-destructive">{errors.timezone.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="gender">Gender</Label>
              <Controller
                name="gender"
                control={control}
                render={({ field }) => (
                  <Select
                    disabled={!isEditMode || isSaving || isUploading}
                    onValueChange={field.onChange}
                    value={field.value || undefined}
                  >
                    <SelectTrigger id="gender" className="bg-background/40">
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Male">Male</SelectItem>
                      <SelectItem value="Female">Female</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                      <SelectItem value="Prefer Not to Say">Prefer Not to Say</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.gender && <p className="text-xs text-destructive">{errors.gender.message}</p>}
            </div>
          </CardContent>
        </Card>

        {/* Birth Details */}
        <Card className="glass-card border-white/10 bg-sidebar/5 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              <Compass className="size-5 text-primary" /> Birth Details & Ephemeris
            </CardTitle>
            <CardDescription>Ephemeris calculation criteria for sidereal charts.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="date_of_birth">Date of Birth</Label>
                <div className="relative">
                  <Input
                    id="date_of_birth"
                    type="date"
                    disabled={!isEditMode || isSaving || isUploading}
                    {...register("date_of_birth")}
                    className="bg-background/40"
                  />
                </div>
                {errors.date_of_birth && <p className="text-xs text-destructive">{errors.date_of_birth.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="time_of_birth">Time of Birth</Label>
                <Input
                  id="time_of_birth"
                  type="time"
                  disabled={!isEditMode || isSaving || isUploading}
                  {...register("time_of_birth")}
                  className="bg-background/40"
                />
                {errors.time_of_birth && <p className="text-xs text-destructive">{errors.time_of_birth.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="birth_place">Birth Place</Label>
              <Controller
                name="birth_place"
                control={control}
                render={({ field }) => (
                  <LocationAutocomplete
                    id="birth_place"
                    value={field.value || ""}
                    onChange={field.onChange}
                    disabled={!isEditMode || isSaving || isUploading}
                    placeholder="City, Region, Country"
                    className="bg-background/40"
                    onSelectLocation={(data) => {
                      setValue("birth_place", data.placeName, { shouldDirty: true });
                      setValue("latitude", data.latitude, { shouldDirty: true });
                      setValue("longitude", data.longitude, { shouldDirty: true });
                      if (data.timezone) {
                        setValue("timezone", data.timezone, { shouldDirty: true });
                      }
                    }}
                  />
                )}
              />
              {errors.birth_place && <p className="text-xs text-destructive">{errors.birth_place.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="latitude">Latitude</Label>
                <Input
                  id="latitude"
                  type="text"
                  disabled={!isEditMode || isSaving || isUploading}
                  placeholder="e.g. 28.6139"
                  {...register("latitude")}
                  className="bg-background/40"
                />
                {errors.latitude && <p className="text-xs text-destructive">{errors.latitude.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="longitude">Longitude</Label>
                <Input
                  id="longitude"
                  type="text"
                  disabled={!isEditMode || isSaving || isUploading}
                  placeholder="e.g. 77.2090"
                  {...register("longitude")}
                  className="bg-background/40"
                />
                {errors.longitude && <p className="text-xs text-destructive">{errors.longitude.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="ayanamsa">Preferred Ayanamsa</Label>
              <Controller
                name="ayanamsa"
                control={control}
                render={({ field }) => (
                  <Select
                    disabled={!isEditMode || isSaving || isUploading}
                    onValueChange={field.onChange}
                    value={field.value || undefined}
                  >
                    <SelectTrigger id="ayanamsa" className="bg-background/40">
                      <SelectValue placeholder="Select Ayanamsa" />
                    </SelectTrigger>
                    <SelectContent>
                      {AYANAMSAS.map((a) => (
                        <SelectItem key={a.value} value={a.value}>
                          {a.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.ayanamsa && <p className="text-xs text-destructive">{errors.ayanamsa.message}</p>}
            </div>
          </CardContent>
        </Card>
      </div>
    </form>
  );
}
