"use client";

import { useForm, Controller, Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { CalendarIcon, MapPinIcon, GlobeIcon, ClockIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { birthDataSchema, BirthDataFormData } from "@/validations/astrology";
import { AstrologyService } from "@/services/astrology";
import { Ayanamsa, BirthChartRequest, BirthChartResponse } from "@/types/astrology";

interface BirthDataFormProps {
  onSubmit: (data: BirthChartResponse, birthData: BirthDataFormData) => void;
  isLoading: boolean;
}

export default function BirthDataForm({ onSubmit, isLoading }: BirthDataFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<BirthDataFormData>({
    resolver: zodResolver(birthDataSchema) as unknown as Resolver<BirthDataFormData>,
    defaultValues: {
      ayanamsa: Ayanamsa.LAHIRI,
      house_system: 1,
      timezone: "Asia/Kolkata",
    },
  });

  async function handleFormSubmit(data: BirthDataFormData) {
    try {
      // Map the form's string-typed ayanamsa to the typed enum before
      // passing to the service layer — zod coerces to string, the API wants enum.
      const request: BirthChartRequest = {
        date: new Date(data.date).toISOString(),
        latitude: data.latitude,
        longitude: data.longitude,
        timezone: data.timezone,
        ayanamsa: data.ayanamsa as Ayanamsa,
        house_system: data.house_system,
      };
      const result = await AstrologyService.getBirthChart(request);
      onSubmit(result, data);
    } catch (error) {
      const axiosError = error as import("axios").AxiosError<{ detail: string }>;
      toast.error(axiosError.response?.data?.detail || "Failed to generate birth chart");
    }
  }

  return (
    <Card className="w-full max-w-2xl mx-auto border-white/10 bg-sidebar/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">Birth Details</CardTitle>
        <CardDescription className="text-center text-muted-foreground">
          Enter your birth information to generate your cosmic chart.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="date" className="flex items-center gap-2">
              <CalendarIcon size={16} /> Date & Time
            </Label>
            <Input 
              id="date" 
              type="datetime-local" 
              {...register("date")} 
              className="bg-background/50"
            />
            {errors.date && <p className="text-xs text-destructive">{errors.date.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="timezone" className="flex items-center gap-2">
              <ClockIcon size={16} /> Timezone
            </Label>
            <Input 
              id="timezone" 
              {...register("timezone")} 
              placeholder="Asia/Kolkata"
              className="bg-background/50"
            />
            {errors.timezone && <p className="text-xs text-destructive">{errors.timezone.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="latitude" className="flex items-center gap-2">
              <MapPinIcon size={16} /> Latitude
            </Label>
            <Input 
              id="latitude" 
              type="number" 
              step="any" 
              {...register("latitude")} 
              placeholder="e.g. 28.6139"
              className="bg-background/50"
            />
            {errors.latitude && <p className="text-xs text-destructive">{errors.latitude.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="longitude" className="flex items-center gap-2">
              <GlobeIcon size={16} /> Longitude
            </Label>
            <Input 
              id="longitude" 
              type="number" 
              step="any" 
              {...register("longitude")} 
              placeholder="e.g. 77.2090"
              className="bg-background/50"
            />
            {errors.longitude && <p className="text-xs text-destructive">{errors.longitude.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label>Ayanamsa</Label>
            <Controller
              name="ayanamsa"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select Ayanamsa" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={Ayanamsa.LAHIRI}>Lahiri</SelectItem>
                    <SelectItem value={Ayanamsa.RAMAN}>Raman</SelectItem>
                    <SelectItem value={Ayanamsa.KRISHNAMURTI}>KP (Krishnamurti)</SelectItem>
                    <SelectItem value={Ayanamsa.TRUE_CHITRA}>True Chitra</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            {errors.ayanamsa && <p className="text-xs text-destructive">{errors.ayanamsa.message}</p>}
          </div>

          <div className="space-y-2">
            <Label>House System</Label>
            <Controller
              name="house_system"
              control={control}
              render={({ field }) => (
                <Select 
                  onValueChange={(val) => field.onChange(parseInt(val))} 
                  defaultValue={field.value?.toString()}
                >
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select House System" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">Placidus</SelectItem>
                    <SelectItem value="2">Whole Sign</SelectItem>
                    <SelectItem value="3">Equal House</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            {errors.house_system && <p className="text-xs text-destructive">{errors.house_system.message}</p>}
          </div>
        </div>

        <CardFooter className="px-0 pt-6">
          <Button 
            type="submit" 
            className="w-full py-6 text-lg font-semibold" 
            disabled={isLoading}
          >
            {isLoading ? "Calculating Cosmic Map..." : "Generate Birth Chart"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
